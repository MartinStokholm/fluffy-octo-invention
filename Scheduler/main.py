import logging

from utils import (
    ensure_dir_exists,
    clear_directory,
    generate_timestamped_filename,
)
from setup import (
    parse_arguments,
    setup_logging,
    setup_output_paths,
    load_people,
    load_holidays,
)
from constraints import (
    AbsenceDaysConstraint,
    FixedAssignmentsConstraint,
    TwoNursesPerDayConstraint,
    WorkingDaysConstraint,
    RestPeriodConstraint,
    IncompatiblePeopleConstraint,
    ShiftAllocationBoundsConstraint,
    ShiftBalanceConstraint,
)
from pathlib import Path
from exporter import SpreadsheetExporter, GraphExporter, JsonExporter
from scheduler import Scheduler


def main():
    args = parse_arguments()

    BASE_DIR = Path(__file__).parent.resolve()

    # Setup logging
    setup_logging(args, BASE_DIR, args.logging_output_dir)

    # Setup output paths
    json_output_path, excel_output_path, graph_output_path, logging_output_path = (
        setup_output_paths(args, BASE_DIR)
    )

    # Load people and holidays from JSON
    if args.test:
        people_json_path = BASE_DIR / "input/people-test.json"
        holidays_json_path = BASE_DIR / "input/holidays-test.json"
    else:
        people_json_path = BASE_DIR / "input/people.json"
        holidays_json_path = BASE_DIR / "input/holidays.json"

    holidays = load_holidays(holidays_json_path)
    people = load_people(people_json_path)
    start_date = args.start_date.strftime("%Y-%m-%d")

    logging.info(f"🔄 {args.weeks} weeks | start date: {start_date}")

    # Initialize FixedAssignmentsConstraint
    fixed_assignments = FixedAssignmentsConstraint(holidays=holidays, people=people)

    # Initialize ShiftAllocationBoundsConstraint with fixed shifts
    shift_allocation_bounds = ShiftAllocationBoundsConstraint(
        fixed_shifts=fixed_assignments.fixed_shifts_per_person,
        weekend_shift_tolerance=1,
        total_shift_tolerance=2,
    )

    # Initialize RestPeriodConstraint with reference to FixedAssignmentsConstraint
    rest_period_constraint = RestPeriodConstraint(fixed_assignments=fixed_assignments)

    # Initialize WorkingDaysConstraint with reference to FixedAssignmentsConstraint
    working_days_constraint = WorkingDaysConstraint(fixed_assignments=fixed_assignments)

    # Initialize ShiftBalanceConstraint with desired tolerances and penalty weight
    shift_balance_constraint = ShiftBalanceConstraint(
        overall_tolerance=1,
        weekend_tolerance=1,
        penalty_weight=400,
    )

    constraints = [
        fixed_assignments,
        TwoNursesPerDayConstraint(),
        working_days_constraint,
        rest_period_constraint,
        IncompatiblePeopleConstraint(),
        AbsenceDaysConstraint(),
        shift_balance_constraint,
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

    jsonExporter = JsonExporter(
        output_filepath=str(json_output_path), base_dir=BASE_DIR
    )

    # Export result as JSON
    jsonExporter.export(scheduled_people)

    # Export spreadsheet from JSON result
    exporter = SpreadsheetExporter(
        json_filepath=str(json_output_path),
        output_excel=str(excel_output_path),
        base_dir=BASE_DIR,
        holidays=holidays,
    )
    exporter.export()

    # Export weekend distribution graph from JSON result
    graph_exporter = GraphExporter(
        json_filepath=str(json_output_path),
        output_graph=str(graph_output_path),
        base_dir=BASE_DIR,
    )
    graph_exporter.export()

    logging.info("✅ Done!")


if __name__ == "__main__":
    main()
