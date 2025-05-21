import os
import sys
import pandas as pd
import re

# Define the regex pattern for prefixes, including those ending with : or -
prefix_pattern = r'^(\[.*?\][:-]?|[\w/-]+-\d+[:-]?|[\w/-]+#\d+[:-]?|#\d+[:-]?|Release \d+\.\d+\.\d+[:-]?|\d+\.x[:-]?|[\w/-]+ \d+[:-]?|[\w/-]+-\d+\.\d+\.\d+[:-]?|[\w\d]+[:-])\s*'
pattern = re.compile(prefix_pattern)

# Function to clean the title and return cleaned title and removed prefix
def clean_title(title):
    if not isinstance(title, str) or not title.strip():
        return title, None
    match = pattern.match(title)
    if match:
        removed = match.group(0).strip()
        cleaned = title[match.end():].strip()
        # Remove leading :, -, or spaces
        cleaned = re.sub(r'^[:\-\s]+', '', cleaned)
        return cleaned, removed
    return title, None


input_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Community-Driven_Removed_links'
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Community-Driven_Removed_keys'
os.makedirs(output_dir, exist_ok=True)

csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
log_entries = []

for file in csv_files:
    file_path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'title' not in df.columns:
            print(f"Skipping {file}: 'title' column not found")
            continue
        # Store original titles
        df['original_title'] = df['title']
        # Apply cleaning
        result = df['original_title'].apply(clean_title)
        df['title'], df['removed_prefix'] = zip(*result)
        # Find rows where prefix was removed
        mask = df['removed_prefix'].notna()
        if mask.any():
            log_df = df[mask][['project', 'pr_number', 'original_title', 'title', 'removed_prefix']]
            log_entries.append(log_df)
        # Drop temporary columns
        df = df.drop(['original_title', 'removed_prefix'], axis=1)
        # Save cleaned CSV
        output_path = os.path.join(output_dir, file)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Processed {file}")
    except Exception as e:
        print(f"Error processing {file}: {e}")

if log_entries:
    df_log = pd.concat(log_entries, ignore_index=True)
    log_path = os.path.join(output_dir, 'removed_prefixes.csv')
    df_log.to_csv(log_path, index=False, encoding='utf-8')
    print(f"Saved removed prefixes to {log_path}")
else:
    print("No prefixes were removed from any project.")