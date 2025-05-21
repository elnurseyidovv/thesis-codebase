import os
import sys
import pandas as pd
import re
from nltk.tokenize import word_tokenize
import string
import ssl

# Bypass SSL verification for NLTK
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Ensure NLTK data is downloaded
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')

# Define cleaning function
def clean_description(text):
    if not isinstance(text, str):
        return text
    tokens = word_tokenize(text)
    cleaned_tokens = []
    for token in tokens:
        if '/' in token or '\\' in token:
            continue
        if re.match(r'^\w+(?:\.\w+)+$', token):
            continue
        if re.match(r'^\d+(?:\.\d+)?$', token):
            continue
        if all(c in string.punctuation for c in token):
            continue
        cleaned_tokens.append(token)
    cleaned_text = ' '.join(cleaned_tokens)
    return cleaned_text

input_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_keys'
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_chars_paths_numbers'
os.makedirs(output_dir, exist_ok=True)

csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
log_entries = []

for file in csv_files:
    file_path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'body' not in df.columns:
            print(f"Skipping {file}: 'body' column not found")
            continue
        # Store original bodies
        df['original_body'] = df['body']
        # Apply cleaning
        df['body'] = df['original_body'].apply(clean_description)
        # Find rows where body was changed
        mask = df['original_body'] != df['body']
        if mask.any():
            log_df = df[mask][['project', 'pr_number', 'original_body', 'body']]
            log_entries.append(log_df)
        # Drop temporary column
        df = df.drop('original_body', axis=1)
        # Save cleaned CSV
        output_path = os.path.join(output_dir, file)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Processed {file}")
    except Exception as e:
        print(f"Error processing {file}: {e}")

if log_entries:
    df_log = pd.concat(log_entries, ignore_index=True)
    log_path = os.path.join(output_dir, 'cleaned_description_logs.csv')
    df_log.to_csv(log_path, index=False, encoding='utf-8')
    print(f"Saved cleaning logs to {log_path}")
else:
    print("No descriptions were cleaned in any project.")