import csv
from openpyxl import Workbook

# Load the CSV data
with open("test.csv", "r") as f:
    reader = csv.reader(f, delimiter=',')
    data = [row for row in reader]

# Create a new workbook and select the active worksheet
wb = Workbook()
ws = wb.active

# Populate the worksheet with the CSV data
for row in data:
    ws.append(row)

# Save the workbook as an XLSX file
wb.save("test.xlsx")

print("CSV has been converted to XLSX and saved as test.xlsx.")
