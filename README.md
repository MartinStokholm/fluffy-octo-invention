# People Schedule Generator

A Python-based tool to generate people schedules, ensuring fair distribution of weekend assignments while respecting availability and compatibility constraints. Furthermore accepts a list of predefined holiday shift allocations.

### Rules and Conditions

The script follows these rules and conditions when generating the schedule:

- **Two people to cover a shift** Each day will be assigned two people to cover that shift.
- **Recovering period**: Each person must have a recovery period of two days (48 hours) from having completed a shift until the next assignment.
- **Compatibility**: Some people have overlapping skillsets, which is why two people can only be assigned for the same day if they are compatible.
- **Working day**: Each person has a predefined work day. The weekdays range from Monday to Thursday, which are the only days they can be assigned to during weekdays.
- **Weekend Assignments**: The script ensures fair distribution of weekend assignments. Each person should be distributed evenly over Fridays, Saturdays, and Sundays.
- **Holidays**: A list of predefined shift allocations takes precedence over normal scheduling.

### The Scheduler

The scheduler uses Google's OR-Tools to solve the scheduling problem by applying various constraints to ensure fairness and feasibility. The constraints include:

- **FixedAssignmentsConstraint** Ensure that the holidays list is respected and takes precedence over other possible assigment configurations.
- **TwoNursesPerDayConstraint**: Ensures exactly two nurses are assigned per day.
- **WorkingDaysConstraint**: Ensures each person only works on their chosen working day or on Friday, Saturday, or Sunday.
- **RestPeriodConstraint**: Ensures at least 48 hours of rest after a shift.
- **IncompatiblePeopleConstraint**: Ensures incompatible people are not assigned on the same day.
- **ShiftAllocationBoundsConstraint**: Balances the number of shifts assigned to each person aswell as among all people. This ensures a fair distribution regarding the total amount of weekend days and week days.
- **ShiftBalanceConstraint**: Balances the number of weekend and weekday shifts, aswell as assuring no one is assigned two consecutive weekends.

### Installation

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

```bash
python main.py --start-date YYYY-MM-DD --weeks N [options]
```

#### [options]

- `--start-date`

  - **Type**: str
  - **Required**: Yes
  - **Description**: Start date in YYYY-MM-DD format.

- `--weeks`

  - **Type**: int
  - **Required**: Yes
  - **Description**: Number of weeks to generate schedules for.

- `--json-output-dir`

  - **Type**: str
  - **Default**: data
  - **Description**: Relative directory to save the JSON output.

- `--excel-output-dir`

  - **Type**: str
  - **Default**: output
  - **Description**: Relative directory to save the Excel schedule.

- `--clean`
- - **Action**: store_true
  - **Description**: Clear the data and output directories before running.

- `--test`
- - **Action** store_true
  - **Description**: Uses test data set without any incompatible pairs.

### Input Files

Ensure that the following JSON files are placed in the input folder:

- `people.json`: People to assign.
- `holidays.json`: Lists of holidays which have predifined assignments.

  **_Optionally_**

- `people-test.json`: Currated list for testing.
- `holidays-tst.json`: Currated list for testing
