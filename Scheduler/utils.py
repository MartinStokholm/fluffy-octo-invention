from datetime import datetime, timedelta


def is_holiday_day(date_obj, holidays):
    return any(date_obj.date() == h.date() for h in holidays)


def can_work_day(person, date_obj):
    # Return False if date_obj is in person's 'unavailable_days'
    date_str = date_obj.strftime("%Y-%m-%d")
    return date_str not in person.get("unavailable_days", [])


def not_incompatible(p1, p2):
    # Return False if p2 is in p1's 'incompatible_with' or vice versa
    return (p2["name"] not in p1.get("incompatible_with", [])) and (
        p1["name"] not in p2.get("incompatible_with", [])
    )


def add_months(start_date, months):
    # Simple logic to add months
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, 28)  # to handle month-end
    return datetime(year, month, day)
