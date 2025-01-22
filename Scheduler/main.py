from datetime import datetime
from scheduler import Scheduler
from person import Person
from schedule_exporter import ScheduleExporter
from result_saver import SaveOutput
from pathlib import Path
import argparse
import json
import logging
from utils import (
    setup_logging,
    ensure_dir_exists,
    generate_timestamped_filename,
    clear_directory,
)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Scheduling Script")
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
    parser.add_argument(
        "--json-output-dir",
        type=str,
        default="data",
        help="Relative directory to save the JSON output",
    )
    parser.add_argument(
        "--excel-output-dir",
        type=str,
        default="output",
        help="Relative directory to save the Excel schedule",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear the data and output directories before running",
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
    setup_logging()

    args = parse_arguments()
    start_date = args.start_date
    weeks = args.weeks
    isCleanRun = args.clean

    BASE_DIR = Path(__file__).parent.resolve()

    # Define output directories based on BASE_DIR
    json_output_dir = BASE_DIR / args.json_output_dir
    excel_output_dir = BASE_DIR / args.excel_output_dir

    if isCleanRun:
        # Clear the directories if --clean flag is set
        clear_directory(json_output_dir)
        clear_directory(excel_output_dir)

    # Ensure output directories exist
    ensure_dir_exists(
        json_output_dir / "do-we-exist.txt"
    )  # Using dummy file to get parent directory
    ensure_dir_exists(excel_output_dir / "do-we-exist.txt")

    # Generate timestamped filenames
    json_output_filename = generate_timestamped_filename(
        "people_assigned", start_date, "json"
    )
    excel_output_filename = generate_timestamped_filename(
        "schedule", start_date, "xlsx"
    )

    # Define full paths with timestamped filenames
    json_output_path = json_output_dir / json_output_filename
    excel_output_path = excel_output_dir / excel_output_filename

    logging.info(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
    logging.info(f"Number of Weeks: {weeks}")
    logging.info(f"JSON Output Path: {json_output_path}")
    logging.info(f"Excel Output Path: {excel_output_path}")

    # Load people from people.json (assumed to be in the same directory as main.py)
    people_json_path = BASE_DIR / "input/people.json"
    people = load_people(people_json_path)

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
    scheduled_people = scheduler.assign_days()

    if scheduled_people is None:
        logging.error("No feasible solution found. Exiting.")
        return

    # Initialize SaveOutput with the desired JSON output path
    saver = SaveOutput(output_filepath=str(json_output_path))
    # Save the assignments using SaveOutput
    saver.save(scheduled_people)

    # After scheduling, export the results to a spreadsheet
    exporter = ScheduleExporter(
        json_filepath=str(json_output_path), output_excel=str(excel_output_path)
    )
    exporter.export()


if __name__ == "__main__":
    main()
