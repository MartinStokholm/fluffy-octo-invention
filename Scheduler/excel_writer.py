import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

def save_schedule_to_excel(assignments, weekend_counts, days_order, personas, filename="people_schedule.xlsx"):
    df = pd.DataFrame(assignments)
    df['date_obj'] = pd.to_datetime(df['date'])
    df['week_number'] = df['date_obj'].dt.isocalendar().week
    df['weekday'] = df['date_obj'].dt.day_name()
    df = df.sort_values(by=['week_number', 'date_obj'])

    # Group assignments by week
    weeks_data = {}
    for _, row in df.iterrows():
        w = int(row['week_number'])
        day = row['weekday']  # Monday, Tuesday, ...
        date_str = row['date']  # 'YYYY-MM-DD'
        assigned = f"{row['person1']}\n{row['person2']}"
        if w not in weeks_data:
            weeks_data[w] = {}
        weeks_data[w][day] = {'date': date_str, 'assignment': assigned}
    
    # Ensure all days are present in each week
    for week in weeks_data:
        for day in days_order:
            if day not in weeks_data[week]:
                # Assign default values for missing days
                weeks_data[week][day] = {'date': 'N/A', 'assignment': 'No Assignment'}

    # Create Excel workbook
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Schedule"

    row_idx = 1

    # Define border style
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))

    # Define fill colors
    holiday_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Light red
    unassigned_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Light yellow
    unassigned_both_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")  # Red

    for week in sorted(weeks_data.keys()):
        # Merge cells for "Week X"
        sheet.merge_cells(start_row=row_idx, end_row=row_idx, start_column=1, end_column=len(days_order))
        week_cell = sheet.cell(row=row_idx, column=1, value=f"Week {week}")
        
        # Apply bold font and centered alignment to the merged cell
        week_cell.font = Font(bold=True)
        week_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        week_cell.border = thin_border  # Apply border
        
        row_idx += 1

        # Add Date Row
        for col_idx, day_name in enumerate(days_order, start=1):
            date = weeks_data[week][day_name]['date']
            date_cell = sheet.cell(row=row_idx, column=col_idx, value=date)
            date_cell.font = Font(bold=True)
            date_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            date_cell.border = thin_border  # Apply border
        row_idx += 1

        # Create weekday header row
        for col_idx, day_name in enumerate(days_order, start=1):
            header_cell = sheet.cell(row=row_idx, column=col_idx, value=day_name)
            header_cell.font = Font(bold=True)
            header_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            header_cell.border = thin_border  # Apply border
        row_idx += 1

        # Fill row with assigned pairs
        for col_idx, day_name in enumerate(days_order, start=1):
            assignment = weeks_data[week].get(day_name, {"assignment": "No Assignment"})['assignment']
            assignment_cell = sheet.cell(
                row=row_idx,
                column=col_idx,
                value=assignment
            )
            assignment_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            assignment_cell.border = thin_border  # Apply border

            # Apply fill color based on assignment status
            if assignment == "Holiday":
                assignment_cell.fill = holiday_fill
            elif assignment == "No Assignment":
                assignment_cell.fill = unassigned_fill
            elif assignment == "Unassigned\nUnassigned":
                assignment_cell.fill = unassigned_both_fill

        row_idx += 1  # Move to the next row for the next week

    # Add Stats Rows
    row_idx += 1  # Add an empty row before stats
    stats_title = f"Weekend Assignment Stats (Total Weeks: {len(weeks_data)})"
    sheet.merge_cells(start_row=row_idx, end_row=row_idx, start_column=1, end_column=5)
    stats_cell = sheet.cell(row=row_idx, column=1, value=stats_title)
    stats_cell.font = Font(bold=True)
    stats_cell.alignment = Alignment(horizontal='left', vertical='center')
    row_idx += 1

    # Header for stats
    sheet.cell(row=row_idx, column=1, value="Person Name").font = Font(bold=True)
    sheet.cell(row=row_idx, column=2, value="Weekend Assignments").font = Font(bold=True)
    sheet.cell(row=row_idx, column=3, value="Week Numbers").font = Font(bold=True)
    sheet.cell(row=row_idx, column=4, value="Unavailable Dates").font = Font(bold=True)
    sheet.cell(row=row_idx, column=5, value="Incompatible With").font = Font(bold=True)
    for col in range(1, 6):
        cell = sheet.cell(row=row_idx, column=col)
        cell.alignment = Alignment(horizontal='left', vertical='center')
        cell.border = thin_border
    row_idx += 1

    # Populate stats
    for person in personas:
        name = person['name']
        unavailable_dates = ", ".join(person.get('unavailable_days', []))
        incompatible_with = ", ".join(person.get('incompatible_with', []))
        weekend_data = weekend_counts.get(name, {'count': 0, 'weeks': []})
        weekend_count = weekend_data['count']
        week_numbers = ", ".join(map(str, sorted(set(weekend_data['weeks']))))

        sheet.cell(row=row_idx, column=1, value=name).alignment = Alignment(horizontal='left', vertical='center')
        sheet.cell(row=row_idx, column=2, value=weekend_count).alignment = Alignment(horizontal='left', vertical='center')
        sheet.cell(row=row_idx, column=3, value=week_numbers).alignment = Alignment(horizontal='left', vertical='center')
        sheet.cell(row=row_idx, column=4, value=unavailable_dates).alignment = Alignment(horizontal='left', vertical='center')
        sheet.cell(row=row_idx, column=5, value=incompatible_with).alignment = Alignment(horizontal='left', vertical='center')
        for col in range(1, 6):
            cell = sheet.cell(row=row_idx, column=col)
            cell.border = thin_border
        row_idx += 1

    # Adjust column widths for better readability
    # Adjust Schedule Sheet Columns
    for i, column in enumerate(days_order, start=1):
        column_letter = get_column_letter(i)
        sheet.column_dimensions[column_letter].width = 20  # Adjust the width as needed

    # Adjust Stats Section Columns
    sheet.column_dimensions[get_column_letter(1)].width = 20  # Person Name
    sheet.column_dimensions[get_column_letter(2)].width = 25  # Weekend Assignments
    sheet.column_dimensions[get_column_letter(3)].width = 30  # Week Numbers
    sheet.column_dimensions[get_column_letter(4)].width = 30  # Unavailable Dates
    sheet.column_dimensions[get_column_letter(5)].width = 30  # Incompatible With

    # Adjust row heights 
    for row in sheet.iter_rows():
        sheet.row_dimensions[row[0].row].height = 30  # Set row height to 30

    # Save as .xlsx
    try:
        wb.save(filename)
        print(f"Schedule successfully generated and saved as '{filename}'.")
    except Exception as e:
        print(f"Failed to save the schedule: {e}")
        sys.exit(1)