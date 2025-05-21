import statistics

def calculate_stats(arr):
    mean = statistics.mean(arr)
    median = statistics.median(arr)
    std_dev = statistics.stdev(arr)
    return {'mean': mean, 'median': median, 'std_dev': std_dev}

if __name__ == "__main__":
    array = []
    for a in array:
        stats = calculate_stats(a)
        if isinstance(stats, dict):
            print(f"Mean: {stats['mean']}")
            print(f"Median: {stats['median']}")
            print(f"Standard Deviation: {stats['std_dev']}")
        else:
            print(stats)