import json
import random
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
import argparse


class Person:
    def __init__(self, name, available_days, incompatible_with):
        self.name = name
        self.available_days = available_days
        self.incompatible_with = incompatible_with
        self.weekend_shifts = defaultdict(int)  # Tracks shifts per weekend day


class Scheduler:
    def __init__(self, personas_file, start_date, num_weeks):
        with open(personas_file, "r") as file:
            data = json.load(file)
        self.people = [
            Person(
                person["name"],
                [person["working_day"]],  # Use working_day as available_days
                person.get("incompatible_with", []),
            )
            for person in data
        ]
        self.schedule = defaultdict(list)
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.num_weeks = num_weeks

    def assign_pairs(self):
        for week in range(self.num_weeks):
            for day_offset in range(7):
                current_date = self.start_date + timedelta(weeks=week, days=day_offset)
                day_name = current_date.strftime("%A")

                if day_name in ["Monday", "Tuesday", "Wednesday"]:
                    self.assign_weekday(current_date, day_name)
                elif day_name in ["Friday", "Saturday", "Sunday"]:
                    self.assign_weekend(current_date, day_name)

    def assign_weekday(self, current_date, day_name):
        available = [p for p in self.people if day_name in p.available_days]
        random.shuffle(available)
        pairs = []

        if len(available) < 2:
            print(
                f"Not enough available people for {day_name} on {current_date.strftime('%Y-%m-%d')}"
            )
            return

        # Attempt to find a compatible pair
        for i in range(len(available)):
            for j in range(i + 1, len(available)):
                p1, p2 = available[i], available[j]
                if (
                    p2.name not in p1.incompatible_with
                    and p1.name not in p2.incompatible_with
                ):
                    pairs.append((p1.name, p2.name))
                    # Remove assigned people
                    del available[j]
                    del available[i]
                    break
            if len(pairs) == 1:
                break

        self.schedule[current_date] = pairs

    def assign_weekend(self, current_date, day_name):
        # Sort people by the number of shifts they have for the specific weekend day
        available = self.people.copy()
        available.sort(key=lambda p: p.weekend_shifts[day_name])
        pairs = []

        if len(available) < 2:
            print(
                f"Not enough available people for {day_name} on {current_date.strftime('%Y-%m-%d')}"
            )
            return

        # Attempt to find a compatible pair prioritizing fairness
        for i in range(len(available)):
            for j in range(i + 1, len(available)):
                p1, p2 = available[i], available[j]
                if (
                    p2.name not in p1.incompatible_with
                    and p1.name not in p2.incompatible_with
                ):
                    pairs.append((p1.name, p2.name))
                    # Increment weekend shift counts
                    p1.weekend_shifts[day_name] += 1
                    p2.weekend_shifts[day_name] += 1
                    # Remove assigned people
                    del available[j]
                    del available[i]
                    break
            if len(pairs) == 1:
                break

        self.schedule[current_date] = pairs

    def export_to_excel(self, output_file):
        data = []
        for date, pairs in sorted(self.schedule.items()):
            week_number = (date - self.start_date).days // 7 + 1
            data.append(
                [
                    f"Week {week_number}",
                    date.strftime("%Y-%m-%d"),
                    ", ".join([" & ".join(pair) for pair in pairs]),
                ]
            )
        df = pd.DataFrame(data, columns=["Week", "Date", "Assigned Pairs"])
        df.to_excel(output_file, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate work schedules.")
    parser.add_argument("start_date", help="Start date in YYYY-MM-DD format")
    parser.add_argument("num_weeks", type=int, help="Number of weeks to generate")
    args = parser.parse_args()

    scheduler = Scheduler("personas.json", args.start_date, args.num_weeks)
    scheduler.assign_pairs()
    scheduler.export_to_excel("schedule.xlsx")
