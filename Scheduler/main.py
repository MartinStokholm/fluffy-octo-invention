import json
import logging

from utils import (
    parse_arguments,
    setup_logging,
    setup_output_paths,
    ensure_dir_exists,
    generate_timestamped_filename,
    clear_directory,
    load_people,
    load_holidays,
)
from constraints import (
    FixedAssignmentsConstraint,
    TwoNursesPerDayConstraint,
    WorkingDaysConstraint,
    RestPeriodConstraint,
    IncompatiblePeopleConstraint,
    ShiftAllocationBoundsConstraint,
    ShiftBalanceConstraint,
)
from person import Person
from pathlib import Path
from datetime import datetime
from exporter import SpreadsheetExporter, GraphExporter
from scheduler import Scheduler
from result_saver import SaveOutput


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

    logging.info(f"🔄 {args.weeks} weeks | start date: {start_date}")

    # Load people and holidays from JSON
    if args.test:
        people_json_path = BASE_DIR / "input/people-test.json"
        holidays_json_path = BASE_DIR / "input/holidays-test.json"
    else:
        people_json_path = BASE_DIR / "input/people.json"
        holidays_json_path = BASE_DIR / "input/holidays.json"

    holidays = load_holidays(holidays_json_path)
    people = load_people(people_json_path)

    # Initialize FixedAssignmentsConstraint
    fixed_assignments = FixedAssignmentsConstraint(holidays=holidays, people=people)

    # Initialize ShiftAllocationBoundsConstraint with fixed shifts
    shift_allocation_bounds = ShiftAllocationBoundsConstraint(
        fixed_shifts=fixed_assignments.fixed_shifts_per_person
    )

    # Initialize RestPeriodConstraint with reference to FixedAssignmentsConstraint
    rest_period_constraint = RestPeriodConstraint(fixed_assignments=fixed_assignments)

    # Initialize WorkingDaysConstraint with reference to FixedAssignmentsConstraint
    working_days_constraint = WorkingDaysConstraint(fixed_assignments=fixed_assignments)

    # Initialize ShiftBalanceConstraint with desired tolerances and penalty weight
    shift_balance_constraint = ShiftBalanceConstraint(
        overall_tolerance=4,  # Tight tolerance to reduce spread
        weekend_tolerance=4,  # Tight weekend distribution
        penalty_weight=200,  # High penalty to discourage consecutive weekends
    )

    # Define all constraints, ensuring FixedAssignmentsConstraint is first
    constraints = [
        fixed_assignments,  # Add fixed assignments first
        TwoNursesPerDayConstraint(),
        working_days_constraint,  # Updated WorkingDaysConstraint
        rest_period_constraint,  # Updated RestPeriodConstraint
        IncompatiblePeopleConstraint(),
        shift_balance_constraint,  # Updated ShiftBalanceConstraint
        shift_allocation_bounds,
    ]

    # Initialize Scheduler with all constraints
    scheduler = Scheduler(
        people=people,
        start_date=args.start_date,
        weeks=args.weeks,
        constraints=constraints,
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
