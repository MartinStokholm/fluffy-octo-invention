# -*- coding: utf-8 -*-

from datetime import datetime


class Person:
    def __init__(self, name, working_day, absence_days):
        # Name of the person
        self.name = name
        # List of people that the person cannot work with given overlapping skillsets
        self.incompatible_with = []
        # The name of the weekday that the person is available to work (eg. Monday, Tuesday, Wednesday, or Thursday)
        self.working_day = working_day
        # Optional list of dates that the person is unavailable to work
        self.absence_days = absence_days
        # List of dates that the person has been assigned to work
        self.schedule = []
        # Count for each weekend day that the person has been assigned to work
        self.fridays_count = 0
        self.saturdays_count = 0
        self.sundays_count = 0

    def assign_shift(self, shift_date: datetime):
        self.schedule.append(shift_date)
        day_name = shift_date.strftime("%A")
        if day_name == "Friday":
            self.fridays_count += 1
        elif day_name == "Saturday":
            self.saturdays_count += 1
        elif day_name == "Sunday":
            self.sundays_count += 1

    def get_last_shift(self):
        if self.schedule:
            return self.schedule[-1]
        return None
