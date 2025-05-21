import os
import sys
import pandas as pd
import re

# Define regex patterns
url_pattern = re.compile(r'http[s]?://\S+')
email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
hash_pattern = re.compile(r'\b[a-fA-F0-9]{32,}\b')

patterns = [
    (url_pattern, 'URL'),
    (email_pattern, 'Email'),
    (hash_pattern, 'Hash')
]

def clean_description(row):
    text = row['body']
    if not isinstance(text, str):
        return text, []
    original = text
    removed = []
    for pattern, name in patterns:
        matches = pattern.findall(text)
        if matches:
            removed.extend([f"{name}: {m}" for m in matches])
        text = pattern.sub('', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text, removed

input_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_README'
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_links'

os.makedirs(output_dir, exist_ok=True)

csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
removed_texts = []

for file in csv_files:
    file_path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'body' not in df.columns or 'project' not in df.columns or 'pr_number' not in df.columns:
            print(f"Skipping {file}: required columns not found")
            continue
        cleaned_bodies = []
        for index, row in df.iterrows():
            cleaned_body, removed = clean_description(row)
            cleaned_bodies.append(cleaned_body)
            if removed:
                removed_texts.append({
                    'project': row['project'],
                    'pr_number': row['pr_number'],
                    'original_body': row['body'] if isinstance(row['body'], str) else '',
                    'removed_text': '; '.join(removed)
                })
        df['body'] = cleaned_bodies
        output_path = os.path.join(output_dir, file)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Processed {file}: cleaned {len(df)} rows")
    except Exception as e:
        print(f"Error processing {file}: {e}")

if removed_texts:
    removed_df = pd.DataFrame(removed_texts)
    removed_path = os.path.join(output_dir, 'removed_texts.csv')
    removed_df.to_csv(removed_path, index=False, encoding='utf-8')
    print(f"Saved {len(removed_texts)} removed text entries to {removed_path}")
else:
    print("No text was removed from any project.")