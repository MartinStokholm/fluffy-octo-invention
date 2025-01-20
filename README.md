# People Schedule Generator

A Python-based tool to generate people schedules, ensuring fair distribution of weekend assignments while respecting availability and compatibility constraints.

### Rules and Conditions

The script follows these rules and conditions:

- **Recovering period** Each person must have a recovery period of two days 48 hours, from having completed a shift until the next assigment.
- **Compatibility**: Some people have overlapping skillsets, which is why two people can only be assigned for the same day if they are compatible.
- **Holidays**: No assignments are made on holidays.
- **Working day** Each person has a predefined work day. The weekdays range from monday to thursday, which is the only day they can be assigned to during weekdays.
- **Weekend Assignments**: The script ensures fair distribution of weekend assignments. Each person should be distributed evenly over fridays, saturdays and sundays.

The generated schedule is saved as `people_schedule.xlsx`, and any errors are logged in `schedule_errors.log`.
