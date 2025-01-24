import json
import shutil
import logging
import argparse
from utils import (
    ensure_dir_exists,
    clear_directory,
    generate_timestamped_filename,
)
from typing import Union, Tuple, List
from person import Person
from pathlib import Path
from argparse import Namespace
from datetime import datetime


def setup_logging(args: Namespace, base_dir: Path, logging_output_dir: Path):
    """
    Configures the logging module to log INFO messages to the console and to a
    timestamped log file within the 'logs' directory.

    :param args: Parsed command-line arguments.
    :param base_dir: The base directory of the project.

    """
    # Ensure the 'logs' directory exists
    logs_dir = base_dir / logging_output_dir
    ensure_dir_exists(
        logs_dir / "do-we-exist.txt", base_dir, is_setup=True
    )  # Using dummy file to get parent directory

    # Generate timestamped log filename using args.start_date
    log_filename = generate_timestamped_filename("scheduler", args.start_date, "log")
    log_filepath = logs_dir / log_filename

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,  # Set to DEBUG for more detailed logs
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),  # Logs to console
            logging.FileHandler(str(log_filepath)),  # Logs to the timestamped file
        ],
    )

    logging.info(f"📝 Logging initiated")


def setup_output_paths(
    args: Namespace, base_dir: Path
) -> Tuple[Path, Path, Path, Path]:
    """
    Sets up the output directories, generates timestamped filenames, defines full paths,
    and logs the relevant information.

    :param args: Parsed command-line arguments.
    :param base_dir: The base directory of the project.
    :return: Tuple containing JSON, Excel and Graph output paths.
    """
    start_date = args.start_date
    is_clean_run = args.clean

    # Define output directories based on BASE_DIR
    json_output_dir = base_dir / args.json_output_dir
    excel_output_dir = base_dir / args.excel_output_dir
    graph_output_dir = base_dir / args.graph_output_dir
    logging_output_dir = base_dir / args.logging_output_dir

    # Ensure output directories exist
    ensure_dir_exists(
        json_output_dir / "do-we-exist.txt", base_dir, is_setup=is_clean_run
    )
    ensure_dir_exists(
        excel_output_dir / "do-we-exist.txt", base_dir, is_setup=is_clean_run
    )
    ensure_dir_exists(
        graph_output_dir / "do-we-exist.txt", base_dir, is_setup=is_clean_run
    )
    ensure_dir_exists(
        logging_output_dir / "do-we-exist.txt", base_dir, is_setup=is_clean_run
    )

    if is_clean_run:
        # Clear the directories if --clean flag is set
        clear_directory(json_output_dir, base_dir)
        clear_directory(excel_output_dir, base_dir)
        clear_directory(graph_output_dir, base_dir)

    # Generate timestamped filenames
    json_output_filename = generate_timestamped_filename(
        "people_assigned", start_date, "json"
    )
    excel_output_filename = generate_timestamped_filename(
        "schedule", start_date, "xlsx"
    )
    graph_output_filename = generate_timestamped_filename(
        "weekend_distribution", start_date, "png"
    )
    logging_output_filename = generate_timestamped_filename(
        "logging", start_date, "log"
    )

    # Define full paths with timestamped filenames
    json_output_path = json_output_dir / json_output_filename
    excel_output_path = excel_output_dir / excel_output_filename
    graph_output_path = graph_output_dir / graph_output_filename
    logging_output_path = logging_output_dir / logging_output_filename

    return json_output_path, excel_output_path, graph_output_path, logging_output_path


def load_people(filepath):
    with filepath.open("r", encoding="utf-8") as file:
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
    logging.info(f"📄 Found {len(people)} people")
    return people


def load_holidays(holidays_filepath: Path) -> List[dict]:
    if not holidays_filepath.exists():
        logging.error(f"Holidays file not found at: {holidays_filepath}")
        return []
    with holidays_filepath.open("r", encoding="utf-8") as file:
        try:
            holidays = json.load(file)
            logging.info(f"📄 Found {len(holidays)} holidays")
            return holidays
        except json.JSONDecodeError as e:
            logging.error(f"⚠️ Error decoding JSON from holidays file: {e}")
            return []


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
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the script using a test dataset",
    )
    return parser.parse_args()
