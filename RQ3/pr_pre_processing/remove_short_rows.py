import os
import sys
import pandas as pd

# Check for command-line argument
input_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_stop_words'
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_short_rows'

os.makedirs(output_dir, exist_ok=True)

# Find all CSV files ending in "_prs.csv"
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
removed_list = []

# Process each CSV file
for file in csv_files:
    file_path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'title' not in df.columns or 'body' not in df.columns:
            print(f"Skipping {file}: missing 'title' or 'body' column")
            continue
        # Calculate combined length
        combined_length = df['title'].fillna('').str.len() + df['body'].fillna('').str.len()
        # Mask for rows to keep
        mask = combined_length >= 5
        df_keep = df[mask]
        df_removed = df[~mask]
        # Save cleaned CSV
        output_path = os.path.join(output_dir, file)
        df_keep.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Processed {file}: removed {len(df_removed)} rows")
        # Collect removed rows
        if not df_removed.empty:
            removed_list.append(df_removed)
    except Exception as e:
        print(f"Error processing {file}: {e}")

# Save removed rows
if removed_list:
    df_all_removed = pd.concat(removed_list, ignore_index=True)
    log_path = os.path.join(output_dir, 'removed_short_rows.csv')
    df_all_removed.to_csv(log_path, index=False, encoding='utf-8')
    print(f"Saved {len(df_all_removed)} removed rows to {log_path}")
else:
    print("No rows were removed from any project.")