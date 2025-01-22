import json
import os
from pathlib import Path
from typing import List
from dataclasses import asdict
from person import Person
from utils import ensure_dir_exists
import logging


class SaveOutput:
    def __init__(self, output_filepath: str = "data/people_assigned.json"):
        self.output_filepath = Path(output_filepath)

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
        with self.output_filepath.open("w") as outfile:
            json.dump(assignments, outfile, indent=4)

        logging.info(f"Assignments successfully saved to:\n{self.output_filepath}.")
