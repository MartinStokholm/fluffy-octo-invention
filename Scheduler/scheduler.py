import sys
from datetime import datetime, timedelta
import random
from collections import defaultdict
from config import load_config
from utils import is_holiday_day, can_work_day, not_incompatible, add_months
from excel_writer import save_schedule_to_excel

def main():
    # Define the order of days
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Check for correct usage
    if len(sys.argv) < 3:
        print("Usage: python schedule.py YYYY-MM-DD number_of_months")
        sys.exit(1)

    start_date_str = sys.argv[1]
    months_str = sys.argv[2]

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
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

    # Load configuration
    config = load_config('Scheduler/personas.json')
    personas = config.get('personas', [])
    holidays = [datetime.strptime(h, '%Y-%m-%d') for h in config.get('holidays', [])]

    if not personas:
        print("No personas found in configuration.")
        sys.exit(1)

    # Initialize next_available for each persona
    for p in personas:
        p['next_available'] = datetime.min

    # Define the schedule period based on the number of months
    end_date = add_months(start_date, number_of_months)
    assignments = []
    errors = []
    next_best_candidates = []

    # Initialize weekend assignment counts with week numbers
    weekend_counts = {persona['name']: {'count': 0, 'weeks': []} for persona in personas}

    # Initialize pairing frequency tracker
    pairing_frequency = defaultdict(int)

    current = start_date
    last_assigned_pair = (None, None)
    while current <= end_date:
        if not is_holiday_day(current, holidays):
            # Gather available candidates
            candidates = [p for p in personas
                          if p['next_available'] <= current and can_work_day(p, current)]
            
            # Ensure at least two candidates are available
            if len(candidates) < 2:
                errors.append(f"{current.strftime('%Y-%m-%d')} ({current.strftime('%A')}): Not enough available people.")
                assignments.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'person1': "Unassigned",
                    'person2': "Unassigned"
                })
                next_best_candidates.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'person1': find_next_best_candidate(personas, current, assignments),
                    'person2': find_next_best_candidate(personas, current, assignments, exclude=[find_next_best_candidate(personas, current, assignments)])
                })
                current += timedelta(days=1)
                continue

            # Shuffle candidates to introduce randomness
            random.shuffle(candidates)

            # Attempt to find a compatible pair
            possible_pairs = []
            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):
                    if not_incompatible(candidates[i], candidates[j]):
                        possible_pairs.append((candidates[i], candidates[j]))

            if not possible_pairs:
                errors.append(f"{current.strftime('%Y-%m-%d')} ({current.strftime('%A')}): No compatible person pairs available.")
                assignments.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'person1': "Unassigned",
                    'person2': "Unassigned"
                })
                next_best_candidates.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'person1': find_next_best_candidate(personas, current, assignments),
                    'person2': find_next_best_candidate(personas, current, assignments, exclude=[find_next_best_candidate(personas, current, assignments)])
                })
                current += timedelta(days=1)
                continue

            # Sort pairs by their frequency to prioritize less frequently paired individuals
            possible_pairs.sort(key=lambda pair: pairing_frequency[(pair[0]['name'], pair[1]['name'])] + pairing_frequency[(pair[1]['name'], pair[0]['name'])])

            # Select a pair that is not the same as the last assigned pair
            chosen_pair = None
            for pair in possible_pairs:
                if (pair[0]['name'], pair[1]['name']) != last_assigned_pair and (pair[1]['name'], pair[0]['name']) != last_assigned_pair:
                    chosen_pair = pair
                    break

            if not chosen_pair:
                chosen_pair = possible_pairs[0]

            assignments.append({
                'date': current.strftime('%Y-%m-%d'),
                'person1': chosen_pair[0]['name'],
                'person2': chosen_pair[1]['name']
            })

            # Update next_available for the assigned people
            chosen_pair[0]['next_available'] = current + timedelta(days=5)
            chosen_pair[1]['next_available'] = current + timedelta(days=5)

            # Update weekend counts if it's a weekend
            if current.weekday() >= 5:  # Saturday=5, Sunday=6
                week_number = current.isocalendar()[1]
                weekend_counts[chosen_pair[0]['name']]['count'] += 1
                weekend_counts[chosen_pair[0]['name']]['weeks'].append(week_number)
                weekend_counts[chosen_pair[1]['name']]['count'] += 1
                weekend_counts[chosen_pair[1]['name']]['weeks'].append(week_number)

            # Update pairing frequency
            pairing_frequency[(chosen_pair[0]['name'], chosen_pair[1]['name'])] += 1
            pairing_frequency[(chosen_pair[1]['name'], chosen_pair[0]['name'])] += 1

            # Update last assigned pair
            last_assigned_pair = (chosen_pair[0]['name'], chosen_pair[1]['name'])

        else:
            # Holidays: No assignment needed
            assignments.append({
                'date': current.strftime('%Y-%m-%d'),
                'person1': "Holiday",
                'person2': "Holiday"
            })

        current += timedelta(days=1)

    # Save the schedule to an Excel file
    save_schedule_to_excel(assignments, weekend_counts, days_order, personas, next_best_candidates)

    # Log errors to a separate file
    if errors:
        try:
            with open("schedule_errors.log", "w") as log_file:
                log_file.write("Scheduling completed with some issues:\n")
                log_file.write("The following days could not be fully assigned and need manual handling:\n")
                for error in errors:
                    log_file.write(f" - {error}\n")
            print("\nSome days could not be fully assigned. See 'schedule_errors.log' for details.")
        except Exception as e:
            print(f"Failed to write error log: {e}")
    else:
        print("\nAll days were successfully scheduled.")

def find_next_best_candidate(personas, current_date, assignments, exclude=[]):
    for p in personas:
        if p['name'] not in exclude and can_work_day(p, current_date):
            return p['name']
    return "No Candidate"

if __name__ == "__main__":
    main()