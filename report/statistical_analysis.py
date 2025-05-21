import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt

# Read the CSV files
df_ind = pd.read_csv('/Users/elnurseyidov/Desktop/Projects/mean-median/Industry-Backed.csv', sep=';')
df_com = pd.read_csv('/Users/elnurseyidov/Desktop/Projects/mean-median/Community-Driven.csv', sep=';')

# Extract the mean scores
means_ind = df_ind['mean'].values
means_com = df_com['mean'].values

# Calculate descriptive statistics
mean_ind = np.mean(means_ind)
std_ind = np.std(means_ind, ddof=1)
n_ind = len(means_ind)

mean_com = np.mean(means_com)
std_com = np.std(means_com, ddof=1)
n_com = len(means_com)

# Perform two-sample t-test
t_stat, p_value = ttest_ind(means_ind, means_com, equal_var=True)

# Calculate Cohen's d
pooled_sd = np.sqrt(((n_ind - 1) * std_ind**2 + (n_com - 1) * std_com**2) / (n_ind + n_com - 2))
d = (mean_ind - mean_com) / pooled_sd

# Print results
print(f"Industry-Backed: mean = {mean_ind:.4f}, std = {std_ind:.4f}, n = {n_ind}")
print(f"Community-Driven: mean = {mean_com:.4f}, std = {std_com:.4f}, n = {n_com}")
print(f"Difference in means = {mean_ind - mean_com:.4f}")
print(f"T-test: t = {t_stat:.4f}, p = {p_value:.4f}")
print(f"Cohen's d = {d:.4f}")

# Visualization: Boxplot
plt.figure(figsize=(8,6))
plt.boxplot([means_ind, means_com], tick_labels=['Industry-Backed', 'Community-Driven'])
plt.ylabel('Mean Readability Score')
plt.title('Comparison of Mean Readability Scores')
plt.savefig('boxplot.png')