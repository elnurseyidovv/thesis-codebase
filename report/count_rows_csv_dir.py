import os
import csv

directory = ''

for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        try:
            with open(os.path.join(directory, filename), 'r', newline='') as f:
                reader = csv.reader(f)
                row_count = sum(1 for row in reader)
            print(f"{filename}: {row_count} rows")
        except Exception as e:
            print(f"file error")