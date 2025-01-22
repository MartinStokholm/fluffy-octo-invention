import os
import shutil
from pathlib import Path
from typing import Union
from datetime import datetime
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,  # Set to DEBUG for more detailed logs
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),  # Logs to console
            logging.FileHandler("scheduler.log"),  # Logs to a file
        ],
    )


def ensure_dir_exists(file_path: Union[str, Path]):
    """
    Ensures that the directory for the given file path exists.
    If it does not exist, the directory (and any necessary parent directories) is created.

    :param file_path: The file path for which to ensure the directory exists.
    """
    path = Path(file_path)
    output_dir = path.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory:\n{output_dir}")


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


def clear_directory(directory_path: Union[str, Path]):
    """
    Clears all contents of the specified directory.

    :param directory_path: The path of the directory to be cleared.

    """
    path = Path(directory_path)
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        logging.info(f"Cleared directory: {path}")
    else:
        logging.info(f"Directory does not exist and cannot be cleared: {path}")

    # Recreate the empty directory
    path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Recreated empty directory: {path}")
