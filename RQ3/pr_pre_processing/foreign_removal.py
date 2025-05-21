import os
import pandas as pd
import regex

# Define directories
input_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_Template'
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_Foreign'
os.makedirs(output_dir, exist_ok=True)

# Function to calculate the ratio of non-Latin letters
def non_latin_letter_ratio(text):
    if not isinstance(text, str):
        return 0
    letters = regex.findall(r'\p{L}', text)
    if not letters:
        return 0
    non_latin = [c for c in letters if not regex.match(r'\p{script=Latin}', c)]
    return len(non_latin) / len(letters)

# Function to determine if row should be kept
def is_mostly_english_row(row, threshold=0.2):
    title_ratio = non_latin_letter_ratio(row['title'])
    body_ratio = non_latin_letter_ratio(row['body']) if pd.notna(row['body']) else 0
    return title_ratio <= threshold and body_ratio <= threshold

# Get all CSV files ending with _prs.csv
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

# List to hold removed rows
removed_list = []

for csv_file in csv_files:
    file_path = os.path.join(input_dir, csv_file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'project' not in df.columns or 'title' not in df.columns or 'body' not in df.columns:
            print(f"Skipping {csv_file}: required columns not found")
            continue
        # Apply the filter
        df_kept = df[df.apply(is_mostly_english_row, axis=1)]
        df_removed = df[~df.apply(is_mostly_english_row, axis=1)]
        # Save kept rows
        output_path = os.path.join(output_dir, csv_file)
        df_kept.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Processed {csv_file}: kept {len(df_kept)} rows, removed {len(df_removed)} rows")
        # Collect removed rows
        if not df_removed.empty:
            removed_list.append(df_removed[['project', 'title', 'body']])
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")

# Save all removed rows
if removed_list:
    df_all_removed = pd.concat(removed_list, ignore_index=True)
    all_removed_path = os.path.join(output_dir, 'removed_non_english.csv')
    df_all_removed.to_csv(all_removed_path, index=False, encoding='utf-8')
    print(f"Saved {len(df_all_removed)} removed rows to {all_removed_path}")
else:
    print("No rows were removed from any project.")