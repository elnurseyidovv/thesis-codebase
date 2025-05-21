import os
import sys
import pandas as pd

input_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_Foreign'
output_dir = '/Users/elnurseyidov/Desktop/Projects-PRs/Industry-Backed_Removed_README'
os.makedirs(output_dir, exist_ok=True)

removed_list = []

for filename in os.listdir(input_dir):
    if filename.endswith('.csv'):
        file_path = os.path.join(input_dir, filename)
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            if 'title' not in df.columns:
                print(f"Skipping {filename}: 'title' column not found")
                continue
            mask = df['title'].str.contains(r'\breadme\b', case=False, na=False, regex=True)
            df_removed = df[mask]
            df_kept = df[~mask]
            output_path = os.path.join(output_dir, filename)
            df_kept.to_csv(output_path, index=False, encoding='utf-8')
            print(f"Processed {filename}: kept {len(df_kept)} rows, removed {len(df_removed)} rows")
            if not df_removed.empty:
                removed_list.append(df_removed)
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if removed_list:
    df_all_removed = pd.concat(removed_list, ignore_index=True)
    all_removed_path = os.path.join(output_dir, 'removed_readme_rows.csv')
    df_all_removed.to_csv(all_removed_path, index=False, encoding='utf-8')
    print(f"Saved {len(df_all_removed)} removed rows to {all_removed_path}")
else:
    print("No rows were removed from any project.")