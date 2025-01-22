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
    setup_output_paths,
    ensure_dir_exists,
    generate_timestamped_filename,
    clear_directory,
    load_people,
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


def main():
    args = parse_arguments()

    BASE_DIR = Path(__file__).parent.resolve()

    if args.clean:
        # Clear the logs and output directories if --clean flag is set
        clear_directory(BASE_DIR / "logs", BASE_DIR, is_setup=True)

    # Setup logging
    setup_logging(args, BASE_DIR)

    # Setup output paths
    json_output_path, excel_output_path = setup_output_paths(args, BASE_DIR)

    logging.info(
        f"🔄 {args.weeks} weeks starting on {args.start_date.strftime('%Y-%m-%d')}"
    )
    # Load people from JSON
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
        # TotalShiftBalanceConstraint(),
        ShiftAllocationBoundsConstraint(),
        ShiftBalanceConstraint(),
        # WeekendDayBalanceConstraint(),
    ]

    # Initialize Scheduler
    scheduler = Scheduler(
        people, start_date=args.start_date, weeks=args.weeks, constraints=constraints
    )

    # Assign days (solve the model)
    scheduled_people = scheduler.assign_days()

    # If no feasible solution is found, exit the script
    if scheduled_people is None:
        logging.error("No feasible solution found. Exiting.")
        return

    # Initialize SaveOutput with the desired JSON output path and BASE_DIR
    saver = SaveOutput(output_filepath=str(json_output_path), base_dir=BASE_DIR)

    # Save the assignments using SaveOutput
    saver.save(scheduled_people)

    # After scheduling, export the results to a spreadsheet
    exporter = ScheduleExporter(
        json_filepath=str(json_output_path),
        output_excel=str(excel_output_path),
        base_dir=BASE_DIR,
    )
    exporter.export()


if __name__ == "__main__":
    main()
