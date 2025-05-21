import os
import sys
import pandas as pd
import emoji

# Function to remove emojis from text
def remove_emojis(text):
    if not isinstance(text, str):
        return text
    cleaned = emoji.replace_emoji(text, '')
    return cleaned.strip()

# Check for command-line argument
input_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Community-Driven_Removed_short_rows'
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Community-Driven_Removed_emojis'
os.makedirs(output_dir, exist_ok=True)

# Find all CSV files ending in "_prs.csv"
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
log_entries = []

# Process each CSV file
for file in csv_files:
    file_path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'title' not in df.columns or 'body' not in df.columns:
            print(f"Skipping {file}: missing 'title' or 'body' column")
            continue
        # Store original columns
        df['original_title'] = df['title']
        df['original_body'] = df['body']
        # Apply emoji removal
        df['title'] = df['title'].apply(remove_emojis)
        df['body'] = df['body'].apply(remove_emojis)
        # Find rows where title or body changed
        mask = (df['original_title'] != df['title']) | (df['original_body'] != df['body'])
        if mask.any():
            log_df = df[mask][['project', 'pr_number', 'original_title', 'title', 'original_body', 'body']]
            log_entries.append(log_df)
        # Drop temporary columns
        df = df.drop(['original_title', 'original_body'], axis=1)
        # Save cleaned CSV
        output_path = os.path.join(output_dir, file)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Processed {file}")
    except Exception as e:
        print(f"Error processing {file}: {e}")

# Save log entries
if log_entries:
    df_log = pd.concat(log_entries, ignore_index=True)
    log_path = os.path.join(output_dir, 'cleaned_emojis_log.csv')
    df_log.to_csv(log_path, index=False, encoding='utf-8')
    print(f"Saved log to {log_path}")
else:
    print("No changes were made in any project.")