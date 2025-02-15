import json
import shutil
import logging
import argparse
import json

from person import Person
from typing import List, Dict, Union, Tuple
from pathlib import Path
from argparse import Namespace
from datetime import datetime


def sanity_check(people: List[Person], holidays: List[Dict]):
    issues_found = False

    # Check for incompatible people working on the same day
    for holiday in holidays:
        holiday_date = holiday["date"]
        people_names = holiday["people_names"]
        for i, person_name in enumerate(people_names):
            person = next(p for p in people if p.name == person_name)
            incompatible_with = person.incompatible_with
            for other_person_name in people_names[i + 1 :]:
                if other_person_name in incompatible_with:
                    logging.warning(
                        f"Incompatible people assigned on {holiday_date}: {person_name} and {other_person_name}"
                    )
                    issues_found = True

    # Check for absence days conflicts
    for person in people:
        name = person.name
        absence_days = person.absence_days
        for holiday in holidays:
            holiday_date = holiday["date"]
            if holiday_date in absence_days and name in holiday["people_names"]:
                logging.warning(
                    f"Person {name} is assigned on their absence day {holiday_date}"
                )
                issues_found = True

    # Check for working day conflicts
    for person in people:
        name = person.name
        working_day = person.working_day
        for holiday in holidays:
            holiday_date = holiday["date"]
            holiday_day_name = datetime.strptime(holiday_date, "%Y-%m-%d").strftime(
                "%A"
            )
            if holiday_day_name != working_day and name in holiday["people_names"]:
                logging.warning(
                    f"Person {name} is assigned on a non-working day {holiday_date} ({holiday_day_name})"
                )
                issues_found = True

    if not issues_found:
        logging.info(
            "No issues found in the provided people.json and holidays.json files."
        )
    else:
        logging.warning(
            "Issues were found in the provided people.json and holidays.json files."
        )


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
                    f"🧹 Removed directory: {get_relative_path(path, base_dir)}"
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
            logging.info(f"🗂️  Created directory: {get_relative_path(path, base_dir)}")
    except Exception as e:
        if not is_setup:
            logging.error(
                f"⚠️ Failed to Created directory: {get_relative_path(path, base_dir)}: {e}"
            )
