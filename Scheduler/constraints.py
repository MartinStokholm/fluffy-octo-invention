import logging

from abc import ABC, abstractmethod
from typing import List
from person import Person
from datetime import datetime, timedelta
from ortools.sat.python import cp_model


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


class FixedAssignmentsConstraint(Constraint):
    def __init__(self, holidays: List[dict], people: List[Person]):
        self.holidays = holidays
        self.people = people
        self.person_name_to_index = {
            person.name: idx for idx, person in enumerate(people)
        }
        self.fixed_shifts_per_person = [0] * len(
            people
        )  # Initialize fixed shifts count
        self.fixed_assignments = set()  # To track (person_index, day_index) tuples

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
        for holiday in self.holidays:
            holiday_date_str = holiday.get("date", "")
            holiday_people = holiday.get("people_names", [])

            # Convert holiday_date_str to datetime object
            try:
                holiday_date = datetime.strptime(holiday_date_str, "%Y-%m-%d")
            except ValueError:
                logging.error(f"Invalid date format for holiday: {holiday_date_str}")
                continue

            try:
                # Find the index of the holiday date
                d = day_dates.index(holiday_date)
            except ValueError:
                logging.warn(
                    f"Holiday date {holiday_date_str} is out of the scheduling range."
                )
                continue

            if len(holiday_people) != 2:
                logging.error(
                    f"Holiday '{holiday.get('holiday_name', 'Unnamed')}' does not have exactly two assigned people."
                )
                continue

            p_indices = []
            for name in holiday_people:
                if name not in self.person_name_to_index:
                    logging.error(
                        f"Person '{name}' in holiday '{holiday.get('holiday_name', 'Unnamed')}' not found in people list."
                    )
                    continue
                p = self.person_name_to_index[name]
                p_indices.append(p)
                self.fixed_shifts_per_person[p] += 1  # Increment fixed shifts
                self.fixed_assignments.add((p, d))  # Track fixed assignment

            if len(p_indices) != 2:
                logging.error(
                    f"Could not assign all people for holiday '{holiday.get('holiday_name', 'Unnamed')}'."
                )
                continue

            # Assign the two people to work on the holiday date
            for p in p_indices:
                model.Add(shifts[(p, d)] == 1)

            # Ensure that no other person is assigned to work on the holiday date
            for p in range(num_people):
                if p not in p_indices:
                    model.Add(shifts[(p, d)] == 0)

            logging.info(
                f"📅 {holiday.get('holiday_name', 'Unnamed')}\t({holiday_date_str})\t➡{holiday_people} "
            )

    def is_fixed_shift(self, p: int, d: int) -> bool:
        """
        Check if a shift for person p on day d is fixed.

        :param p: Person index
        :param d: Day index
        :return: True if the shift is fixed, False otherwise
        """
        return (p, d) in self.fixed_assignments


class TwoNursesPerDayConstraint(Constraint):
    """
    Constraint to ensure that there are exactly two nurses working per day.
    """

    def apply(self, model, shifts, people, day_dates, day_names, num_people, num_days):
        for d in range(num_days):
            model.Add(sum(shifts[(p, d)] for p in range(num_people)) == 2)

        logging.info("🍄 Constraint Applied Successfully: 'Two nurses per Day' ")


class WorkingDaysConstraint(Constraint):
    """
    Constraint to ensure that each person only works on their chosen working day
    or on Friday, Saturday, or Sunday, unless the shift is fixed by FixedAssignmentsConstraint.
    """

    def __init__(self, fixed_assignments: FixedAssignmentsConstraint):
        """
        Initialize with a reference to FixedAssignmentsConstraint to identify fixed shifts.

        :param fixed_assignments: Instance of FixedAssignmentsConstraint.
        """
        self.fixed_assignments = fixed_assignments

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
        allowed_weekends = {"Friday", "Saturday", "Sunday"}

        for p in range(num_people):
            person = people[p]
            preferred_day = person.working_day.strip()
            allowed_days = {preferred_day}.union(allowed_weekends)

            for d in range(num_days):
                day_name = day_names[d]
                if day_name not in allowed_days:
                    # Only enforce if this shift is NOT fixed
                    if not self.fixed_assignments.is_fixed_shift(p, d):
                        model.Add(shifts[(p, d)] == 0)

        logging.info("🍄 Constraint Applied Successfully: 'Working Days'")


class RestPeriodConstraint(Constraint):
    def __init__(self, fixed_assignments: FixedAssignmentsConstraint):
        """
        Initialize with a reference to FixedAssignmentsConstraint to identify fixed shifts.

        :param fixed_assignments: Instance of FixedAssignmentsConstraint.
        """
        self.fixed_assignments = fixed_assignments

    def apply(
        self,
        model: cp_model.CpModel,
        shifts: dict,
        people: List["Person"],  # Assuming Person is defined elsewhere
        day_dates: List[datetime],
        day_names: List[str],
        num_people: int,
        num_days: int,
    ):
        for p in range(num_people):
            for d in range(
                num_days - 2
            ):  # Ensure at least 2 days of rest after a shift
                # Reference to the shift variable on day d
                shift_var = shifts[(p, d)]

                # Create literals for the shift being assigned
                is_shift_assigned = shift_var

                # Enforce no work on day d+1 and d+2 if shift on day d is assigned
                model.Add(shifts[(p, d + 1)] == 0).OnlyEnforceIf(is_shift_assigned)
                model.Add(shifts[(p, d + 2)] == 0).OnlyEnforceIf(is_shift_assigned)

        logging.info("🍄 Constraint Applied Successfully: 'Rest Period'")


class IncompatiblePeopleConstraint(Constraint):
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
        logging.info("🍄 Constraint Applied Successfully: 'Incompatible People'")


class ShiftAllocationBoundsConstraint(Constraint):
    def __init__(
        self,
        fixed_shifts: List[int],
        total_shift_tolerance: int = 2,
        weekend_shift_tolerance: int = 2,
    ):
        """
        Initialize with the number of fixed shifts per person.

        :param fixed_shifts: A list where each index corresponds to a person and the value is the number of fixed shifts assigned.
        """
        self.fixed_shifts = fixed_shifts
        self.total_shift_tolerance = total_shift_tolerance
        self.weekend_shift_tolerance = weekend_shift_tolerance

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
        # Calculate total shifts required
        total_shifts_required = num_days * 2  # 2 nurses per day
        expected_shifts = total_shifts_required // num_people
        tolerance = self.total_shift_tolerance

        # Calculate weekend bounds
        weekend_days = {"Friday", "Saturday", "Sunday"}
        total_weekend_days = sum(1 for day in day_names if day in weekend_days)
        weekend_shifts_required = total_weekend_days * 2  # 2 nurses per weekend day
        expected_weekend_shifts = weekend_shifts_required // num_people
        weekend_tolerance = self.weekend_shift_tolerance

        for p in range(num_people):
            # ----- Overall Shifts -----
            person_fixed_shifts = self.fixed_shifts[p]
            min_shifts = max(expected_shifts - tolerance - person_fixed_shifts, 0)
            max_shifts = expected_shifts + tolerance - person_fixed_shifts
            if min_shifts > max_shifts:
                min_shifts = max_shifts

            total_shifts = sum(shifts[(p, d)] for d in range(num_days))
            model.Add(total_shifts >= min_shifts)
            model.Add(total_shifts <= max_shifts)

            # ----- Weekend Shifts -----
            weekend_shifts = sum(
                shifts[(p, d)] for d in range(num_days) if day_names[d] in weekend_days
            )
            min_weekend_shifts = max(expected_weekend_shifts - weekend_tolerance, 0)
            max_weekend_shifts = expected_weekend_shifts + weekend_tolerance

            model.Add(weekend_shifts >= min_weekend_shifts)
            model.Add(weekend_shifts <= max_weekend_shifts)

        logging.info("🍄 Constraint Applied Successfully: 'Shift Allocation Bounds'")


class ShiftBalanceConstraint(Constraint):
    def __init__(
        self,
        overall_tolerance: int = 1,
        weekend_tolerance: int = 1,
        penalty_weight: int = 10,
    ):
        """
        Initialize the ShiftBalanceConstraint with tolerances and penalty weight.

        :param overall_tolerance: Allowed deviation in total shifts per person.
        :param weekend_tolerance: Allowed deviation in shifts across weekend days per person.
        :param penalty_weight: Weight for penalizing consecutive weekend shifts.
        """
        self.overall_tolerance = overall_tolerance
        self.weekend_tolerance = weekend_tolerance
        self.penalty_weight = penalty_weight

    def apply(
        self,
        model: cp_model.CpModel,
        shifts: dict,
        people: List["Person"],
        day_dates: List["datetime"],
        day_names: List[str],
        num_people: int,
        num_days: int,
    ):
        # Define weekend and weekday days
        weekend_days = {"Friday", "Saturday", "Sunday"}
        weekday_days = {"Monday", "Tuesday", "Wednesday", "Thursday"}

        # ===== Overall Shift Balancing =====
        # Calculate total shifts per person
        total_shifts_per_person = []
        for p in range(num_people):
            total_shifts = model.NewIntVar(0, num_days, f"total_shifts_p{p}")
            model.Add(total_shifts == sum(shifts[(p, d)] for d in range(num_days)))
            total_shifts_per_person.append(total_shifts)

        # Calculate expected shifts per person
        # Assuming 2 shifts per day
        total_shifts_required = 2 * num_days
        expected_shifts = total_shifts_required // num_people
        min_shifts = max(expected_shifts - self.overall_tolerance, 0)
        max_shifts = expected_shifts + self.overall_tolerance

        # Enforce total shifts within [min_shifts, max_shifts] for each person
        for p in range(num_people):
            model.Add(total_shifts_per_person[p] >= min_shifts)
            model.Add(total_shifts_per_person[p] <= max_shifts)

        # ===== Weekend Shifts Balancing =====
        # Ensure even distribution across Fridays, Saturdays, and Sundays
        for p in range(num_people):
            # Define variables for each weekend day
            friday_shifts = [
                shifts[(p, d)] for d in range(num_days) if day_names[d] == "Friday"
            ]
            saturday_shifts = [
                shifts[(p, d)] for d in range(num_days) if day_names[d] == "Saturday"
            ]
            sunday_shifts = [
                shifts[(p, d)] for d in range(num_days) if day_names[d] == "Sunday"
            ]

            total_friday = model.NewIntVar(0, len(friday_shifts), f"friday_shifts_p{p}")
            total_saturday = model.NewIntVar(
                0, len(saturday_shifts), f"saturday_shifts_p{p}"
            )
            total_sunday = model.NewIntVar(0, len(sunday_shifts), f"sunday_shifts_p{p}")

            # Sum shifts for each weekend day
            model.Add(total_friday == sum(friday_shifts))
            model.Add(total_saturday == sum(saturday_shifts))
            model.Add(total_sunday == sum(sunday_shifts))

            # Define the difference variables with negative lower bounds
            fr_sat_diff = model.NewIntVar(-num_days, num_days, f"fr_sat_diff_p{p}")
            sat_sun_diff = model.NewIntVar(-num_days, num_days, f"sat_sun_diff_p{p}")
            fr_sun_diff = model.NewIntVar(-num_days, num_days, f"fr_sun_diff_p{p}")

            model.Add(fr_sat_diff == total_friday - total_saturday)
            model.Add(sat_sun_diff == total_saturday - total_sunday)
            model.Add(fr_sun_diff == total_friday - total_sunday)

            # Absolute difference variables stay [0..num_days]
            abs_fr_sat_diff = model.NewIntVar(0, num_days, f"abs_fr_sat_diff_p{p}")
            abs_sat_sun_diff = model.NewIntVar(0, num_days, f"abs_sat_sun_diff_p{p}")
            abs_fr_sun_diff = model.NewIntVar(0, num_days, f"abs_fr_sun_diff_p{p}")

            model.AddAbsEquality(abs_fr_sat_diff, fr_sat_diff)
            model.AddAbsEquality(abs_sat_sun_diff, sat_sun_diff)
            model.AddAbsEquality(abs_fr_sun_diff, fr_sun_diff)

            # Now a difference of -2 or +2 can become abs(...)=2
            model.Add(abs_fr_sat_diff <= self.weekend_tolerance)
            model.Add(abs_sat_sun_diff <= self.weekend_tolerance)
            model.Add(abs_fr_sun_diff <= self.weekend_tolerance)

        # ======= Constraint: Consecutive Weekend Shifts Penalty =====

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
                    # If there are no weekend days in the week, set the variable to 0
                    weekend_shift_vars[(p, week)] = model.NewConstant(0)

        # Add penalties for assigning weekend shifts in consecutive weeks
        consecutive_weekend_penalties = []
        for p in range(num_people):
            for week in range(1, num_weeks):
                prev_week = week - 1
                current_week = week

                # Binary variable that is 1 if both previous and current weeks have weekend shifts
                consecutive_weekend = model.NewBoolVar(
                    f"consecutive_weekend_p{p}_w{current_week}"
                )

                # Define the condition: weekend_shift_prev_week AND weekend_shift_current_week
                model.AddBoolAnd(
                    [
                        weekend_shift_vars[(p, prev_week)],
                        weekend_shift_vars[(p, current_week)],
                    ]
                ).OnlyEnforceIf(consecutive_weekend)

                # Define the negation condition
                model.AddBoolOr(
                    [
                        weekend_shift_vars[(p, prev_week)].Not(),
                        weekend_shift_vars[(p, current_week)].Not(),
                    ]
                ).OnlyEnforceIf(consecutive_weekend.Not())

                # Collect the penalty variable
                consecutive_weekend_penalties.append(consecutive_weekend)

        # Sum all penalties
        total_consecutive_weekend_penalties = model.NewIntVar(
            0, num_people * num_weeks, "total_consecutive_weekend_penalties"
        )
        model.Add(
            total_consecutive_weekend_penalties == sum(consecutive_weekend_penalties)
        )

        # ======= Aggregating Metrics for Objective =======
        # Define the aggregated metric to minimize
        # Aggregated metric includes shift balance differences and penalties
        aggregated_metric = model.NewIntVar(
            0,
            2 * num_days + num_people * num_weeks * self.penalty_weight,
            "aggregated_metric",
        )

        # Calculate: balance_diff * 1 + total_consecutive_weekend_penalties * penalty_weight
        # First, sum all absolute differences
        # Note: balance_diff is already captured by the constraints above,
        # so we don't need to add it explicitly here.

        model.Add(
            aggregated_metric
            == total_consecutive_weekend_penalties * self.penalty_weight
        )

        # ======= Setting the Objective =======
        # Minimize the aggregated metric
        model.Minimize(aggregated_metric)

        logging.info("🍄 Constraint Applied Successfully: 'Shift Balance'")
