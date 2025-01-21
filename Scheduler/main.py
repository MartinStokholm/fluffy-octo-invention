from datetime import datetime
from scheduler import Scheduler
from person import Person
from schedule_exporter import ScheduleExporter
import argparse
import json


def parse_arguments():
    parser = argparse.ArgumentParser(description="Nurse Scheduling Script")
    parser.add_argument(
        "--start-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        required=True,
        help="Number of weeks to generate schedules for",
    )
    return parser.parse_args()


def load_people(filepath):
    with open(filepath, "r") as file:
        data = json.load(file)
    people = []
    for person_data in data:
        person = Person(
            name=person_data["name"],
            working_day=person_data["working_day"],
            absence_days=person_data.get("absence_days", []),
        )
        person.incompatible_with = person_data.get("incompatible_with", [])
        people.append(person)
    return people


def main():
    args = parse_arguments()
    start_date = args.start_date
    weeks = args.weeks
    print(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
    print(f"Number of Weeks: {weeks}")

    # Load people from people.json
    people = load_people("people.json")

    # Define constraints
    from constraints import (
        TwoNursesPerDayConstraint,
        WorkingDaysConstraint,
        RestPeriodConstraint,
        IncompatiblePeopleConstraint,
        ShiftBalanceConstraint,
        WeekendDayBalanceConstraint,
        TotalShiftBalanceConstraint,
        ShiftAllocationBoundsConstraint,
    )

    constraints = [
        TwoNursesPerDayConstraint(),
        WorkingDaysConstraint(),
        RestPeriodConstraint(),
        IncompatiblePeopleConstraint(),
        TotalShiftBalanceConstraint(),
        ShiftAllocationBoundsConstraint(),
        # ShiftBalanceConstraint(),
        # WeekendDayBalanceConstraint(),
    ]

    # Initialize Scheduler
    scheduler = Scheduler(people, start_date, weeks, constraints)

    # Assign days (solve the model)
    scheduler.assign_days()

    # After scheduling, export the results to a spreadsheet
    exporter = ScheduleExporter(
        json_filepath="people_assigned.json", output_excel="schedule.xlsx"
    )
    exporter.export()


if __name__ == "__main__":
    main()
