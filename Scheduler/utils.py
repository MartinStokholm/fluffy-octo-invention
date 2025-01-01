from datetime import datetime, timedelta

def is_holiday_day(date_obj, holidays):
    return any(date_obj.date() == h.date() for h in holidays)

def can_work_day(person, date_obj):
    unavailable_dates = [datetime.strptime(date, '%Y-%m-%d').date() for date in person.get('unavailable_days', [])]
    return date_obj.date() not in unavailable_dates

def not_incompatible(p1, p2):
    return (p1['name'] not in p2.get('incompatible_with', [])) and \
           (p2['name'] not in p1.get('incompatible_with', []))

def add_months(start_date, months):
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, [31,
          29 if year%4==0 and not year%100==0 or year%400==0 else 28,
          31,30,31,30,31,31,30,31,30,31][month-1])
    return datetime(year, month, day)