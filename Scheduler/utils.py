from pathlib import Path
from typing import Union, Tuple
from argparse import Namespace
from datetime import datetime
import logging
import shutil
import json
from person import Person


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

    logging.info(f"📝 Logging: {get_relative_path(log_filepath, base_dir)}")


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
    )  # Using dummy file to get parent directory
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
        clear_directory(logging_output_dir, base_dir)

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


def get_relative_path(path: Path, base_dir: Path) -> str:
    """
    Returns the path relative to base_dir. If path is not under base_dir, returns the absolute path.

    :param path: The Path object to convert.
    :param base_dir: The base directory Path object.
    :return: A string representing the relative or absolute path.
    """
    try:
        relative_path = path.relative_to(base_dir)
        return f"/{relative_path}"
    except ValueError:
        # Path is not under base_dir
        return str(path)


def ensure_dir_exists(file_path: Union[str, Path], base_dir: Path, is_setup=False):
    """
    Ensures that the directory for the given file path exists.
    If it does not exist, the directory (and any necessary parent directories) is created.

    :param file_path: The file path for which to ensure the directory exists.
    :param base_dir: The base directory to compute relative paths.
    """
    path = Path(file_path)
    output_dir = path.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        if not is_setup:
            logging.info(
                f"Created directory: {get_relative_path(output_dir, base_dir)}"
            )
    else:
        if not is_setup:
            logging.debug(
                f"Directory already exists: {get_relative_path(output_dir, base_dir)}"
            )


def generate_timestamped_filename(
    base_name: str, start_date: datetime, extension: str
) -> str:
    """
    Generates a timestamped filename incorporating the start date and current timestamp.

    :param base_name: The base name of the file (e.g., 'people_assigned').
    :param start_date: The start date provided by the user.
    :param extension: The file extension (e.g., 'json', 'xlsx').
    :return: A string representing the timestamped filename.
    """
    current_timestamp = datetime.now().strftime("%H%M%S")
    formatted_start_date = start_date.strftime("%Y-%m-%d")
    filename_suffix = f"{formatted_start_date}_{current_timestamp}"
    return f"{base_name}_{filename_suffix}.{extension}"


def clear_directory(directory_path: Union[str, Path], base_dir: Path, is_setup=False):
    """
    Clears all contents of the specified directory.

    :param directory_path: The path of the directory to be cleared.
    :param base_dir: The base directory to compute relative paths.
    """
    path = Path(directory_path)
    if path.exists() and path.is_dir():
        try:
            shutil.rmtree(path)
            if not is_setup:
                logging.info(
                    f"🧹 Cleared directory: {get_relative_path(path, base_dir)}"
                )
        except Exception as e:
            if not is_setup:
                logging.error(
                    f"⚠️ Failed to clear directory {get_relative_path(path, base_dir)}: {e}"
                )
    else:
        if not is_setup:
            logging.warning(
                f"⚠️ Directory does not exist and cannot be cleared: {get_relative_path(path, base_dir)}"
            )

    # Recreate the empty directory
    try:
        path.mkdir(parents=True, exist_ok=True)
        if not is_setup:
            logging.info(
                f"🗂️  Recreated empty directory: {get_relative_path(path, base_dir)}"
            )
    except Exception as e:
        if not is_setup:
            logging.error(
                f"⚠️ Failed to recreate directory {get_relative_path(path, base_dir)}: {e}"
            )


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
