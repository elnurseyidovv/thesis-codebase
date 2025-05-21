import os
import pandas as pd
import re
from collections import Counter

# Define directories
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Community-Driven_Removed_Bump'
cleaned_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Community-Driven_Removed_Template'
os.makedirs(cleaned_dir, exist_ok=True)


# Function to strip checkbox prefixes
def strip_checkbox(line):
    return re.sub(r'^\s*-\s*\[.\]\s*', '', line)


# List to hold removed template lines
removed_rows = []

# Get all CSV files in output_dir ending with _prs.csv
csv_files = [f for f in os.listdir(output_dir) if f.endswith('_prs_cleaned.csv')]

for csv_file in csv_files:
    print("New CSV is being processed")
    file_path = os.path.join(output_dir, csv_file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'project' not in df.columns or 'body' not in df.columns:
            print(f"Skipping {csv_file}: required columns not found")
            continue
        project_name = df['project'].iloc[0]
        descriptions = df['body'].dropna()

        all_stripped_lines = []
        stripped_to_original = {}

        for desc in descriptions:
            lines = desc.split('\n')
            for line in lines:
                stripped = strip_checkbox(line)
                all_stripped_lines.append(stripped)
                if stripped not in stripped_to_original:
                    stripped_to_original[stripped] = set()
                stripped_to_original[stripped].add(line)

        freq = Counter(all_stripped_lines)
        T = 100 # Threshold: at least 10 or 10% of descriptions
        template_stripped = {stripped for stripped, count in freq.items() if count >= T}

        # Collect unique original template lines
        template_lines = set()
        for stripped in template_stripped:
            template_lines.update(stripped_to_original[stripped])

        # For removed templates
        for line in template_lines:
            removed_rows.append({'project': project_name, 'template_line': line})


        # Filter descriptions
        def filter_description(desc):
            if pd.isna(desc):
                return desc
            lines = desc.split('\n')
            kept_lines = [line for line in lines if strip_checkbox(line) not in template_stripped]
            return '\n'.join(kept_lines)


        df['body'] = df['body'].apply(filter_description)

        # Save cleaned CSV
        cleaned_path = os.path.join(cleaned_dir, csv_file.replace('.csv', '_cleaned.csv'))
        df.to_csv(cleaned_path, index=False, encoding='utf-8')
        print(
            f"Processed {csv_file}: cleaned {len(descriptions)} descriptions, identified {len(template_lines)} template lines")
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")

# Save removed templates
if removed_rows:
    removed_df = pd.DataFrame(removed_rows)
    removed_df.to_csv(os.path.join(cleaned_dir, 'all_removed_templates.csv'), index=False, encoding='utf-8')
    print(
        f"Saved {len(removed_rows)} removed template lines to {os.path.join(cleaned_dir, 'all_removed_templates.csv')}")
else:
    print("No template lines were removed from any project.")