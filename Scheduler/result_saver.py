import json
import logging
from utils import ensure_dir_exists, get_relative_path
from person import Person
from typing import List
from pathlib import Path
from dataclasses import asdict


class SaveOutput:
    def __init__(
        self,
        output_filepath: str = "data/people_assigned.json",
        base_dir: Path = Path("."),
    ):
        self.output_filepath = Path(output_filepath)
        self.base_dir = base_dir

    def save(self, people: List[Person]):
        """
        Saves the assigned shifts and weekend counts for each person to a JSON file.

        :param people: List of Person instances with assigned shifts.
        """
        assignments = []
        for person in people:
            assigned_dates = [
                shift_date.strftime("%Y-%m-%d") for shift_date in person.schedule
            ]
            person_data = {
                "name": person.name,
                "working_day": person.working_day,
                "absence_days": person.absence_days,
                "incompatible_with": person.incompatible_with,
                "assigned_shifts": assigned_dates,
                "fridays_count": person.fridays_count,
                "saturdays_count": person.saturdays_count,
                "sundays_count": person.sundays_count,
            }
            assignments.append(person_data)
        try:
            with self.output_filepath.open("w", encoding="utf-8") as outfile:
                json.dump(assignments, outfile, indent=4, ensure_ascii=False)
            logging.info(
                f"💾 Output: {get_relative_path(self.output_filepath, self.base_dir)}."
            )
        except Exception as e:
            logging.error(
                f"❌ Output: {get_relative_path(self.output_filepath, self.base_dir)}: {e}"
            )
