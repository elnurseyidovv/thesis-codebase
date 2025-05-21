import os
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import norm

# Define the base path
base_path = Path('/Users/elnurseyidov/Desktop/Projects-Centrality')

# Define the groups
groups = ['Industry-Backed', 'Community-Driven']

# Store group statistics for z-test
group_stats = {}

for group in groups:
    print("---------------------------------------------------------------------------------------------------------------")
    print(group)
    group_path = base_path / group
    readability_scores_path = group_path / 'readability_scores'

    # Initialize accumulators for weighted mean and variance
    total_weighted_sum = 0
    total_central_files = 0
    total_variance_sum = 0

    # Get list of centrality CSVs
    centrality_csvs = list(group_path.glob('*_centrality.csv'))

    for centrality_csv in centrality_csvs:
        project_name = centrality_csv.stem.replace('_centrality', '')
        centrality_file = centrality_csv
        readability_file = readability_scores_path / f"{project_name}_readability.csv"

        if not readability_file.exists():
            print(f"Readability file not found for {project_name}")
            continue

        # Read centrality CSV
        try:
            centrality_df = pd.read_csv(centrality_file)
        except Exception as e:
            print(f"Error reading centrality file for {project_name}: {e}")
            continue

        # Select top 10% by pagerank
        N = len(centrality_df)
        top_N = int(np.ceil(N * 0.1))
        selected_files = centrality_df.nlargest(top_N, 'pagerank')['file'].tolist()

        # Extract relative paths: everything after group/
        selected_relative = []
        for path in selected_files:
            if group + '/' in path:
                rel = path.split(group + '/', 1)[1]
                selected_relative.append(rel)
            else:
                print(f"Path {path} does not contain {group}/")

        # Read readability CSV
        try:
            readability_df = pd.read_csv(readability_file)
        except Exception as e:
            print(f"Error reading readability file for {project_name}: {e}")
            continue

        # Filter readability_df where file_name ends with any of selected_relative
        matching_files = readability_df[
            readability_df['file_name'].apply(lambda x: any(x.endswith(rel) for rel in selected_relative))]

        if matching_files.empty:
            print(f"No matching files found for {project_name}")
            mean_score = np.nan
            median_score = np.nan
            std_score = np.nan
        else:
            mean_score = matching_files['score'].mean()
            median_score = matching_files['score'].median()
            std_score = matching_files['score'].std()
            # Accumulate for weighted mean and variance
            if len(matching_files) > 0 and not np.isnan(mean_score):
                total_weighted_sum += mean_score * len(matching_files)
                total_central_files += len(matching_files)
                if not np.isnan(std_score):  # Ensure std_score is valid
                    total_variance_sum += len(matching_files) * (std_score ** 2)

        print(
            f"Processed {project_name}, mean: {mean_score}, median: {median_score}, std: {std_score}, "
            f"selected {len(selected_relative)} files, found {len(matching_files)} matching")

    # Calculate and print group-level statistics
    if total_central_files > 0:
        group_weighted_mean = total_weighted_sum / total_central_files
        group_variance = total_variance_sum / (total_central_files ** 2)
        group_std_error = np.sqrt(group_variance)
        print(f"{group} central files weighted mean: {group_weighted_mean:.6f}")
        print(f"{group} central files variance: {group_variance:.6e}")
        print(f"{group} central files standard error: {group_std_error:.6e}")
        # Store stats for z-test
        group_stats[group] = {
            'weighted_mean': group_weighted_mean,
            'variance': group_variance,
            'total_files': total_central_files
        }
    else:
        print(f"No central files with readability scores found for {group}")
        group_stats[group] = None

# Perform z-test if both groups have valid stats
if group_stats.get('Industry-Backed') and group_stats.get('Community-Driven'):
    mean1 = group_stats['Industry-Backed']['weighted_mean']
    mean2 = group_stats['Community-Driven']['weighted_mean']
    var1 = group_stats['Industry-Backed']['variance']
    var2 = group_stats['Community-Driven']['variance']
    se_diff = np.sqrt(var1 + var2)
    z_stat = (mean1 - mean2) / se_diff
    p_value = 2 * (1 - norm.cdf(abs(z_stat)))  # Two-tailed test
    print("---------------------------------------------------------------------------------------------------------------")
    print("Z-Test for Difference in Weighted Means of Central Files")
    print(f"Industry-Backed mean: {mean1:.6f}, Community-Driven mean: {mean2:.6f}")
    print(f"Difference: {mean1 - mean2:.6f}")
    print(f"Z-statistic: {z_stat:.2f}")
    print(f"P-value: {p_value:.6e}")
else:
    print("Cannot perform z-test: missing data for one or both groups")