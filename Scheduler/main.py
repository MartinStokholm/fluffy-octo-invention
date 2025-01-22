from datetime import datetime
from scheduler import Scheduler
from person import Person
from exporter import SpreadsheetExporter, GraphExporter
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
from constraints import (
    TwoNursesPerDayConstraint,
    WorkingDaysConstraint,
    RestPeriodConstraint,
    IncompatiblePeopleConstraint,
    ShiftAllocationBoundsConstraint,
    ShiftBalanceConstraint,
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
        default="output/data",
        help="Relative directory to save the JSON output",
    )
    parser.add_argument(
        "--excel-output-dir",
        type=str,
        default="output/spreadsheet",
        help="Relative directory to save the Excel schedule",
    ),
    parser.add_argument(
        "--graph-output-dir",
        type=str,
        default="output/graph",
        help="Relative directory to save the assignment distribution graph",
    ),
    parser.add_argument(
        "--logging-output-dir",
        type=str,
        default="output/logging",
        help="Relative directory to save the log files",
    ),
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear the data and output directories before running",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    BASE_DIR = Path(__file__).parent.resolve()

    # Setup logging
    setup_logging(args, BASE_DIR, args.logging_output_dir)

    # Setup output paths
    json_output_path, excel_output_path, graph_output_path, logging_output_path = (
        setup_output_paths(args, BASE_DIR)
    )
    start_date = args.start_date.strftime("%Y-%m-%d")

    logging.info(f"🔄 {args.weeks} weeks | from: {start_date}")

    # Load people from JSON
    people_json_path = BASE_DIR / "input/people.json"
    people = load_people(people_json_path)

    # Define constraints
    constraints = [
        TwoNursesPerDayConstraint(),
        WorkingDaysConstraint(),
        RestPeriodConstraint(),
        IncompatiblePeopleConstraint(),
        ShiftBalanceConstraint(),
        ShiftAllocationBoundsConstraint(),
    ]

    # Initialize Scheduler
    scheduler = Scheduler(
        people, start_date=args.start_date, weeks=args.weeks, constraints=constraints
    )

    # Assign days (solve the model)
    scheduled_people = scheduler.assign_days()

    # If no feasible solution is found, exit the script
    if scheduled_people is None:
        logging.info("❌ No feasible solution found. Exiting.")
        return
    logging.info("🤓 Solution Found!")

    # Initialize SaveOutput with the desired JSON output path and BASE_DIR
    saver = SaveOutput(output_filepath=str(json_output_path), base_dir=BASE_DIR)

    # Save the assignments using SaveOutput
    saver.save(scheduled_people)

    # After scheduling, export the results to a spreadsheet
    exporter = SpreadsheetExporter(
        json_filepath=str(json_output_path),
        output_excel=str(excel_output_path),
        base_dir=BASE_DIR,
    )
    exporter.export()

    # Export the assignment distribution graph
    graph_exporter = GraphExporter(
        json_filepath=str(json_output_path),
        output_graph=str(graph_output_path),
        base_dir=BASE_DIR,
    )
    graph_exporter.export_graph()

    logging.info("✅ Scheduling, export, and graph generation completed successfully.")


if __name__ == "__main__":
    main()
