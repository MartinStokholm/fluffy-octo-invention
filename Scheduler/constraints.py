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


class ShiftAllocationBoundsConstraint(Constraint):
    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        # Calculate expected shifts per person
        total_shifts_required = num_days * 2  # 2 nurses per day
        expected_shifts = total_shifts_required // num_people

        # Define a tolerance level
        tolerance = 10

        for p in range(num_people):
            total_shifts = sum(shifts[(p, d)] for d in range(num_days))
            model.Add(total_shifts >= expected_shifts - tolerance)
            model.Add(total_shifts <= expected_shifts + tolerance)


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

        # ======= New Constraint: Consecutive Weekend Shifts =====
        # Calculate number of weeks
        num_weeks = num_days // 7

        # Define a binary variable for each person-week indicating a weekend shift
        weekend_shift_vars = {}

        for p in range(num_people):
            for week in range(num_weeks):
                week_start = week * 7
                week_end = week_start + 7
                weekend_days_current_week = [
                    d
                    for d in range(week_start, week_end)
                    if day_names[d] in weekend_days
                ]

                if weekend_days_current_week:
                    weekend_shift_vars[(p, week)] = model.NewBoolVar(
                        f"weekend_shift_p{p}_w{week}"
                    )
                    # If any weekend day in the week is assigned, weekend_shift_vars[(p, week)] = 1
                    model.AddMaxEquality(
                        weekend_shift_vars[(p, week)],
                        [shifts[(p, d)] for d in weekend_days_current_week],
                    )
                else:
                    weekend_shift_vars[(p, week)] = model.NewConstant(0)

        # Add penalties for assigning weekend shifts in consecutive weeks
        penalty_weight = 10  # Adjust this weight as needed

        consecutive_weekend_penalties = []

        for p in range(num_people):
            for week in range(1, num_weeks):
                prev_week = week - 1
                current_week = week

                # Binary variable that is 1 if both previous and current weeks have weekend shifts
                consecutive_weekend = model.NewBoolVar(
                    f"consecutive_weekend_p{p}_w{current_week}"
                )
                model.AddBoolAnd(
                    [
                        weekend_shift_vars[(p, prev_week)],
                        weekend_shift_vars[(p, current_week)],
                    ]
                ).OnlyEnforceIf(consecutive_weekend)
                model.AddBoolOr(
                    [
                        weekend_shift_vars[(p, prev_week)].Not(),
                        weekend_shift_vars[(p, current_week)].Not(),
                    ]
                ).OnlyEnforceIf(consecutive_weekend.Not())

                consecutive_weekend_penalties.append(consecutive_weekend)

        # Sum all penalties
        total_consecutive_weekend_penalties = model.NewIntVar(
            0, num_people * num_weeks, "total_consecutive_weekend_penalties"
        )
        model.Add(
            total_consecutive_weekend_penalties == sum(consecutive_weekend_penalties)
        )

        # ===== Aggregate into the main model's objective variables with weighting =====
        weight_shift_balance = 1  # Existing weight
        weight_consecutive_weekends = penalty_weight  # New penalty weight

        if not hasattr(model, "aggregated_diff"):
            model.aggregated_diff = (
                balance_diff * weight_shift_balance
                + total_consecutive_weekend_penalties * weight_consecutive_weekends
            )
        else:
            new_aggregated = model.NewIntVar(
                0,
                2 * num_days * weight_shift_balance
                + num_people * num_weeks * weight_consecutive_weekends,
                "aggregated_diff_new",
            )
            model.Add(
                new_aggregated
                == model.aggregated_diff
                + (balance_diff * weight_shift_balance)
                + (total_consecutive_weekend_penalties * weight_consecutive_weekends)
            )
            model.Add(model.aggregated_diff == new_aggregated)
