import json
from typing import List
from person import Person


class SaveOutput:
    def __init__(self, output_filepath: str = "people_assigned.json"):
        self.output_filepath = output_filepath

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

        with open(self.output_filepath, "w") as outfile:
            json.dump(assignments, outfile, indent=4)

        print(f"Assignments successfully saved to {self.output_filepath}.")
