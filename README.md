# People Schedule Generator

A Python-based tool to generate people schedules, ensuring fair distribution of weekend assignments while respecting availability and compatibility constraints.

## Table of Contents

- [People Schedule Generator](#people-schedule-generator)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Downloading the Repository](#downloading-the-repository)
  - [Installation](#installation)
    - [Installing Dependencies](#installing-dependencies)
  - [Configuration](#configuration)
    - [Personas File](#personas-file)
  - [Usage](#usage)
    - [Running the Script](#running-the-script)
    - [Rules and Conditions](#rules-and-conditions)

## Getting Started

These instructions will help you set up and run the People Schedule Generator on your local machine.

### Downloading the Repository

1. **Download the ZIP File:**

   - Navigate to the [GitHub repository](https://github.com/MartinStokholm/fluffy-octo-invention) page.
   - Click on the green **Code** button.
   - Select **Download ZIP** from the dropdown menu.

2. **Extract the ZIP File:**

   - Locate the downloaded `fluffy-octo-invention-main.zip` file in your `Downloads` folder.
   - Double-click the ZIP file to extract its contents to your desired location.

## Installation

Ensure you have Python installed on your device. This guide assumes you have Python and `pip` pre-installed.

### Installing Dependencies

1. **Open Terminal:**

   - You can open Terminal by navigating to `Applications` > `Utilities` > `Terminal`.

2. **Navigate to the Project Directory:**

   ```bash
   cd path/to/fluffy-octo-invention/Scheduler
   ```

3. **Install Required Packages:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Personas File

The `personas.json` file contains the configuration for the people and holidays. It includes the following sections:

- **personas**: A list of people with their names, incompatible persons, and unavailable days.
- **holidays**: A list of dates that are considered holidays.

Example `personas.json`:

```json
{
  "personas": [
    {
      "name": "Susan",
      "incompatible_with": [],
      "unavailable_days": []
    },
    {
      "name": "Mary",
      "incompatible_with": [],
      "unavailable_days": []
    }
  ],
  "holidays": ["2023-12-25", "2023-01-01"]
}
```

You can modify this file to add or remove people, set incompatibilities, and define unavailable days.

## Usage

### Running the Script

To run the script, use the following command:

```bash
python Scheduler/schedule.py YYYY-MM-DD number_of_months
```

- `YYYY-MM-DD`: The start date for the schedule.
- `number_of_months`: The number of months to generate the schedule for.

Example:

```bash
python Scheduler/schedule.py 2025-01-01 3
```

### Rules and Conditions

The script follows these rules and conditions:

- **Availability**: A person can only be assigned if they are available on that day.
- **Compatibility**: Two people can only be assigned together if they are compatible.
- **Holidays**: No assignments are made on holidays.
- **Weekend Assignments**: The script ensures fair distribution of weekend assignments.

The generated schedule is saved as `people_schedule.xlsx`, and any errors are logged in `schedule_errors.log`.
