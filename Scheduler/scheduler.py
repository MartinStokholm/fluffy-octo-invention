from typing import List
from person import Person
from datetime import datetime, timedelta
from constraints import Constraint
from ortools.sat.python import cp_model
from result_saver import SaveOutput


class Scheduler:
    def __init__(
        self,
        people: List[Person],
        start_date: datetime,
        weeks: int,
        constraints: List[Constraint],
    ):
        self.people = people
        self.start_date = start_date
        self.weeks = weeks
        self.constraints = constraints
        self.model = cp_model.CpModel()
        self.shifts = {}
        self.setup()

    def setup(self):
        num_days = self.weeks * 7
        num_people = len(self.people)
        all_days = [self.start_date + timedelta(days=i) for i in range(num_days)]
        day_dates = [day for day in all_days]
        day_names = [day.strftime("%A") for day in all_days]

        # Create shift variables: shifts[(p, d)] is 1 if person p works on day d, else 0
        for p in range(num_people):
            for d in range(num_days):
                self.shifts[(p, d)] = self.model.NewBoolVar(f"shift_p{p}_d{d}")

        # Apply all constraints
        for constraint in self.constraints:
            constraint.apply(
                self.model,
                self.shifts,
                self.people,
                day_dates,
                day_names,
                num_people,
                num_days,
            )

        # After all constraints have been applied, set the objective to minimize aggregated_diff
        if hasattr(self.model, "aggregated_diff"):
            self.model.Minimize(self.model.aggregated_diff)
        else:
            # If no aggregated_diff exists, define a default objective
            self.model.Minimize(0)

    def assign_days(self):
        # Solve the model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 180.0  # Optional time limit
        solver.parameters.log_search_progress = True
        # solver.parameters.enable_probing = True # DEPRECATED DO NOT USE
        status = solver.Solve(self.model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            print("Solution Found:")
            # Instantiate the SaveOutput class
            saver = SaveOutput()
            # Collect assignments
            assignments = []
            num_people = len(self.people)
            num_days = self.weeks * 7
            day_dates = [self.start_date + timedelta(days=i) for i in range(num_days)]
            day_names = [day.strftime("%A") for day in day_dates]

            for d in range(num_days):
                assigned = [
                    self.people[p].name
                    for p in range(num_people)
                    if solver.Value(self.shifts[(p, d)])
                ]
                shift_date = day_dates[d].strftime("%Y-%m-%d")
                day_name = day_names[d]
                print(f"{shift_date} ({day_name}): {', '.join(assigned)}")
                for p in range(num_people):
                    if solver.Value(self.shifts[(p, d)]):
                        self.people[p].assign_shift(day_dates[d])

            # Save the assignments using SaveOutput
            saver.save(self.people)
            print("Scheduling complete.")
        else:
            print(f"Solver Status: {solver.StatusName(status)}")
            print(f"Number of conflicts: {solver.NumConflicts()}")
            print(f"Branches: {solver.NumBranches()}")
            print(f"Wall time: {solver.WallTime()}s")
            print("No feasible solution found.")
