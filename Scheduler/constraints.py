from abc import ABC, abstractmethod
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
from typing import List
from person import Person
import logging


class Constraint(ABC):
    @abstractmethod
    def apply(
        self,
        model: cp_model.CpModel,
        shifts: dict,
        people: List[Person],
        day_dates: List[datetime],
        day_names: List[str],
        num_people: int,
        num_days: int,
    ):
        pass


class ShiftAllocationBoundsConstraint(Constraint):
    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        # Calculate expected shifts per person
        total_shifts_required = num_days * 2  # 2 nurses per day
        expected_shifts = total_shifts_required // num_people

        # Define a tolerance level
        tolerance = 2

        for p in range(num_people):
            total_shifts = sum(shifts[(p, d)] for d in range(num_days))
            model.Add(total_shifts >= expected_shifts - tolerance)
            model.Add(total_shifts <= expected_shifts + tolerance)


class TotalShiftBalanceConstraint(Constraint):
    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        # Calculate total shifts for each person
        total_shifts = []
        for p in range(num_people):
            person_total = model.NewIntVar(0, num_days, f"total_shifts_p{p}")
            model.Add(person_total == sum(shifts[(p, d)] for d in range(num_days)))
            total_shifts.append(person_total)

        # Define max and min total shifts
        max_total = model.NewIntVar(0, num_days, "max_total_shifts")
        min_total = model.NewIntVar(0, num_days, "min_total_shifts")
        model.AddMaxEquality(max_total, total_shifts)
        model.AddMinEquality(min_total, total_shifts)

        # Calculate the difference
        shift_diff = model.NewIntVar(0, num_days, "total_shift_diff")
        model.Add(shift_diff == max_total - min_total)

        # Aggregate into the main model's objective variables
        if not hasattr(model, "aggregated_diff"):
            model.aggregated_diff = shift_diff
        else:
            # Introduce an intermediate variable to accumulate differences
            new_aggregated = model.NewIntVar(0, num_days * 2, "aggregated_diff_new")
            model.Add(new_aggregated == model.aggregated_diff + shift_diff)
            model.Add(model.aggregated_diff == new_aggregated)


class ShiftBalanceConstraint(Constraint):
    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        # Define weekend and weekday days
        weekend_days = {"Friday", "Saturday", "Sunday"}
        weekday_days = {"Monday", "Tuesday", "Wednesday", "Thursday"}

        # ===== Weekend Shifts Balancing =====
        weekend_max_shifts = model.NewIntVar(0, num_days, "max_weekend_shifts")
        weekend_min_shifts = model.NewIntVar(0, num_days, "min_weekend_shifts")
        weekend_total_shifts = []

        for p in range(num_people):
            weekend_shifts = [
                shifts[(p, d)] for d in range(num_days) if day_names[d] in weekend_days
            ]
            total_weekend = model.NewIntVar(
                0, len(weekend_shifts), f"weekend_shifts_p{p}"
            )
            model.Add(total_weekend == sum(weekend_shifts))
            weekend_total_shifts.append(total_weekend)

        model.AddMaxEquality(weekend_max_shifts, weekend_total_shifts)
        model.AddMinEquality(weekend_min_shifts, weekend_total_shifts)
        weekend_diff = model.NewIntVar(0, num_days, "weekend_diff")
        model.Add(weekend_diff == weekend_max_shifts - weekend_min_shifts)

        # ===== Weekday Shifts Balancing =====
        weekday_max_shifts = model.NewIntVar(0, num_days, "max_weekday_shifts")
        weekday_min_shifts = model.NewIntVar(0, num_days, "min_weekday_shifts")
        weekday_total_shifts = []

        for p in range(num_people):
            weekday_shifts = [
                shifts[(p, d)] for d in range(num_days) if day_names[d] in weekday_days
            ]
            total_weekday = model.NewIntVar(
                0, len(weekday_shifts), f"weekday_shifts_p{p}"
            )
            model.Add(total_weekday == sum(weekday_shifts))
            weekday_total_shifts.append(total_weekday)

        model.AddMaxEquality(weekday_max_shifts, weekday_total_shifts)
        model.AddMinEquality(weekday_min_shifts, weekday_total_shifts)
        weekday_diff = model.NewIntVar(0, num_days, "weekday_diff")
        model.Add(weekday_diff == weekday_max_shifts - weekday_min_shifts)

        # ===== Aggregate Shift Balance Diffs =====
        balance_diff = model.NewIntVar(0, 2 * num_days, "balance_diff")
        model.Add(balance_diff == weekend_diff + weekday_diff)

        # Aggregate into the main model's objective variables with weighting
        weight_shift_balance = 1  # Adjust weight as needed
        if not hasattr(model, "aggregated_diff"):
            model.aggregated_diff = balance_diff * weight_shift_balance
        else:
            new_aggregated = model.NewIntVar(
                0, 2 * num_days * weight_shift_balance, "aggregated_diff_new"
            )
            model.Add(
                new_aggregated
                == model.aggregated_diff + (balance_diff * weight_shift_balance)
            )
            model.Add(model.aggregated_diff == new_aggregated)


class WeekendDayBalanceConstraint(Constraint):
    """
    Constraint to ensure that each weekend day (Friday, Saturday, Sunday) shifts
    are evenly distributed among all employees to maintain fairness.
    """

    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        # Define weekend days
        weekend_days = {"Friday": [], "Saturday": [], "Sunday": []}

        # Categorize days by weekend day name and collect their indices
        for d in range(num_days):
            day_name = day_names[d]
            if day_name in weekend_days:
                weekend_days[day_name].append(
                    d
                )  # List of day indices for each weekend day

        # For each weekend day, balance the number of shifts per person
        for day, day_indices in weekend_days.items():
            if not day_indices:
                continue  # Skip if the day doesn't exist in the schedule

            # For fairness, calculate total shifts per person for this day
            total_shifts_per_person = []
            for p in range(num_people):
                shift_vars = [shifts[(p, d)] for d in day_indices]
                # Each weekend day requires exactly two nurses, so a nurse can have at most one shift per day
                total_shift = model.NewIntVar(0, 1, f"{day}_shifts_p{p}")
                model.Add(total_shift == sum(shift_vars))
                total_shifts_per_person.append(total_shift)

            # Define max and min shifts for fairness on this weekend day
            max_shifts = model.NewIntVar(0, 1, f"max_{day}_shifts")
            min_shifts = model.NewIntVar(0, 1, f"min_{day}_shifts")
            model.AddMaxEquality(max_shifts, total_shifts_per_person)
            model.AddMinEquality(min_shifts, total_shifts_per_person)

            # Calculate the difference for this day
            shift_diff = model.NewIntVar(0, 1, f"{day}_shift_diff")
            model.Add(shift_diff == max_shifts - min_shifts)

            # Aggregate into the main model's objective variables with integer weighting
            weight_weekend_day_balance = 1  # Changed from 0.5 to 1
            if not hasattr(model, "aggregated_diff"):
                model.aggregated_diff = shift_diff * weight_weekend_day_balance
            else:
                new_aggregated = model.NewIntVar(
                    0, len(day_indices) * 2, f"aggregated_diff_new_{day}"
                )
                model.Add(
                    new_aggregated
                    == model.aggregated_diff + (shift_diff * weight_weekend_day_balance)
                )
                model.Add(model.aggregated_diff == new_aggregated)


class TwoNursesPerDayConstraint(Constraint):
    """
    Constraint to ensure that there are exactly two nurses working per day.
    """

    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        for d in range(num_days):
            model.Add(sum(shifts[(p, d)] for p in range(num_people)) == 2)


class WorkingDaysConstraint(Constraint):
    """
    Constraint to ensure that each person only works on their chosen working day
    or on Friday, Saturday, or Sunday.
    """

    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        allowed_weekends = {"Friday", "Saturday", "Sunday"}

        for p in range(num_people):
            person = people[p]
            preferred_day = person.working_day.strip()
            allowed_days = {preferred_day}.union(allowed_weekends)

            for d in range(num_days):
                day_name = day_names[d]
                if day_name not in allowed_days:
                    model.Add(shifts[(p, d)] == 0)


class RestPeriodConstraint(Constraint):
    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        for p in range(num_people):
            for d in range(
                num_days - 2
            ):  # Ensure at least 2 days of rest after a shift
                model.Add(shifts[(p, d)] + shifts[(p, d + 1)] <= 1)
                model.Add(shifts[(p, d)] + shifts[(p, d + 2)] <= 1)


class IncompatiblePeopleConstraint(Constraint):
    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        for p in range(num_people):
            person = people[p]
            incompatible_people = person.incompatible_with
            incompatible_indices = [
                idx
                for idx, other in enumerate(people)
                if other.name in incompatible_people
            ]

            for d in range(num_days):
                for q in incompatible_indices:
                    if q < num_people:  # Ensure valid index
                        model.Add(shifts[(p, d)] + shifts[(q, d)] <= 1)
