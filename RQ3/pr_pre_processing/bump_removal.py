import os
import pandas as pd
import re

# Define directories
input_dir = "/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed"  # Directory containing original CSV files
output_dir = "/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_Bump"  # Directory for removed CSV files
os.makedirs(output_dir, exist_ok=True)

# Define the pairs of words for filtering
pairs = [
    ("bump", "to"),
    ("bumped", "to"),
    ("bump", "up"),
    ("bumped", "up")
]

# List to hold removed DataFrames
removed_dfs = []

# Get all CSV files in input_dir ending with _prs.csv
csv_files = [f for f in os.listdir(input_dir) if f.endswith('_prs.csv')]

for csv_file in csv_files:
    print("New CSV file started to process")
    file_path = os.path.join(input_dir, csv_file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'title' not in df.columns:
            print(f"Skipping {csv_file}: 'title' column not found")
            continue
        # Initialize mask
        mask = pd.Series([False] * len(df), index=df.index)
        for word1, word2 in pairs:
            pattern1 = r'\b' + re.escape(word1) + r'\b'
            pattern2 = r'\b' + re.escape(word2) + r'\b'
            mask |= (df['title'].str.contains(pattern1, case=False, regex=True, na=False) &
                     df['title'].str.contains(pattern2, case=False, regex=True, na=False))
        df_removed = df[mask]
        df_kept = df[~mask]
        # Save kept rows
        base_name, ext = os.path.splitext(csv_file)
        cleaned_base = f"{base_name}_cleaned{ext}"
        output_path = os.path.join(output_dir, cleaned_base)
        df_kept.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Processed {csv_file}: kept {len(df_kept)} rows, removed {len(df_removed)} rows")
        if not df_removed.empty:
            removed_dfs.append(df_removed)
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")

# After processing all files
if removed_dfs:
    df_all_removed = pd.concat(removed_dfs, ignore_index=True)
    all_removed_path = os.path.join(output_dir, 'all_removed_prs.csv')
    df_all_removed.to_csv(all_removed_path, index=False, encoding='utf-8')
    print(f"Saved {len(df_all_removed)} removed rows to {all_removed_path}")
else:
    print("No rows were removed from any project.")