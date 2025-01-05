import sys
import random
from datetime import datetime, timedelta
from collections import defaultdict
from config import load_config
from utils import is_holiday_day, can_work_day, not_incompatible, add_months
from excel_writer import save_schedule_to_excel

REST_DAYS = 2  # 48 hours = 2 days


def assign_weekday(current_date, personas, assignments, errors):
    day_name = current_date.strftime("%A")
    candidates = [
        p
        for p in personas
        if p["working_day"] == day_name and p["next_available"] <= current_date
    ]
    if not candidates:
        assignments.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "person1": "Unassigned",
                "person2": "Unassigned",
            }
        )
        errors.append(current_date.strftime("%Y-%m-%d"))
        return

    if len(candidates) == 1:
        assignments.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "person1": candidates[0]["name"],
                "person2": "None Available",
            }
        )
        candidates[0]["next_available"] = current_date + timedelta(days=REST_DAYS)
        return

    pairs = []
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            if not_incompatible(candidates[i], candidates[j]):
                pairs.append((candidates[i], candidates[j]))

    if not pairs:
        assignments.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "person1": candidates[0]["name"],
                "person2": "None Compatible",
            }
        )
        candidates[0]["next_available"] = current_date + timedelta(days=REST_DAYS)
        return

    p1, p2 = random.choice(pairs)
    assignments.append(
        {
            "date": current_date.strftime("%Y-%m-%d"),
            "person1": p1["name"],
            "person2": p2["name"],
        }
    )
    p1["next_available"] = current_date + timedelta(days=REST_DAYS)
    p2["next_available"] = current_date + timedelta(days=REST_DAYS)


def assign_weekend(current_date, personas, assignments, errors, weekend_counts):
    # All Friday, Saturday, Sunday logic goes here
    weekend_candidates = [p for p in personas if p["next_available"] <= current_date]
    weekend_candidates.sort(key=lambda x: x["weekend_shifts_count"])

    assigned_pair = None
    min_count = (
        weekend_candidates[0]["weekend_shifts_count"] if weekend_candidates else 0
    )
    group_min = [
        p for p in weekend_candidates if p["weekend_shifts_count"] == min_count
    ]

    if len(group_min) < 2:
        group_min = weekend_candidates

    random.shuffle(group_min)

    for i in range(len(group_min)):
        for j in range(i + 1, len(group_min)):
            if not_incompatible(group_min[i], group_min[j]):
                assigned_pair = (group_min[i], group_min[j])
                break
        if assigned_pair:
            break

    if not assigned_pair:
        assignments.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "person1": "Unassigned",
                "person2": "Unassigned",
            }
        )
        errors.append(current_date.strftime("%Y-%m-%d"))
        return

    p1, p2 = assigned_pair
    assignments.append(
        {
            "date": current_date.strftime("%Y-%m-%d"),
            "person1": p1["name"],
            "person2": p2["name"],
        }
    )
    p1["next_available"] = current_date + timedelta(days=REST_DAYS)
    p2["next_available"] = current_date + timedelta(days=REST_DAYS)
    p1["weekend_shifts_count"] += 1
    p2["weekend_shifts_count"] += 1

    # Count which weekend day
    week_day_name = current_date.strftime("%A")
    week_number = current_date.isocalendar()[1]
    for person in (p1, p2):
        weekend_counts[person["name"]]["count"] += 1
        weekend_counts[person["name"]]["weeks"].append(week_number)
        if week_day_name == "Friday":
            weekend_counts[person["name"]]["fridays"] += 1
        elif week_day_name == "Saturday":
            weekend_counts[person["name"]]["saturdays"] += 1
        elif week_day_name == "Sunday":
            weekend_counts[person["name"]]["sundays"] += 1


def main():
    if len(sys.argv) < 3:
        print("Usage: python scheduler.py YYYY-MM-DD number_of_months")
        sys.exit(1)

    start_date_str = sys.argv[1]
    months_str = sys.argv[2]

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        print("Incorrect date format. Please use YYYY-MM-DD.")
        sys.exit(1)

    try:
        number_of_months = int(months_str)
        if number_of_months < 1:
            raise ValueError
    except ValueError:
        print("Number of months must be a positive integer.")
        sys.exit(1)

    config = load_config("Scheduler/personas.json")
    personas = config.get("personas", [])
    holidays = [datetime.strptime(h, "%Y-%m-%d") for h in config.get("holidays", [])]

    if not personas:
        print("No personas found in configuration.")
        sys.exit(1)

    weekend_counts = {
        p["name"]: {"count": 0, "weeks": [], "fridays": 0, "saturdays": 0, "sundays": 0}
        for p in personas
    }

    for p in personas:
        p.setdefault("unavailable_days", [])
        p.setdefault("incompatible_with", [])
        p["next_available"] = datetime.min
        p["weekend_shifts_count"] = 0

    assignments = []
    errors = []

    end_date = add_months(start_date, number_of_months)
    current = start_date

    while current <= end_date:
        if is_holiday_day(current, holidays):
            assignments.append(
                {
                    "date": current.strftime("%Y-%m-%d"),
                    "person1": "Holiday",
                    "person2": "Holiday",
                }
            )
            current += timedelta(days=1)
            continue

        # Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
        weekday_idx = current.weekday()
        if weekday_idx < 4:  # Monday-Thursday
            assign_weekday(current, personas, assignments, errors)
        else:
            # Friday, Saturday, Sunday => handle with assign_weekend
            assign_weekend(current, personas, assignments, errors, weekend_counts)

        current += timedelta(days=1)

    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    save_schedule_to_excel(assignments, weekend_counts, days_order, personas)

    if errors:
        try:
            with open("schedule_errors.log", "w") as f:
                f.write("Days with incomplete assignment:\n")
                for e in errors:
                    f.write(f"{e}\n")
            print("Some days were not fully assigned. See schedule_errors.log.")
        except Exception as e:
            print(f"Failed to write schedule_errors.log: {e}")


if __name__ == "__main__":
    main()
