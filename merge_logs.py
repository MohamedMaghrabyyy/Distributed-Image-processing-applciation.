from datetime import datetime
import os

def merge_and_sort_logs(log_file1, log_file2, merged_log_file):
    try:
        # Read contents of both log files
        with open(log_file1, 'r') as file1, open(log_file2, 'r') as file2:
            log1 = file1.readlines()
            log2 = file2.readlines()

        # Merge logs
        merged_log = log1 + log2

        # Filter out lines that do not contain valid timestamps
        merged_log = [line for line in merged_log if line.startswith('2')]

        # Sort logs by timestamp in descending order
        merged_log.sort(key=lambda x: datetime.strptime(x.split(' - ')[0], '%Y-%m-%d %H:%M:%S,%f'), reverse=True)

        # Write merged and sorted log to the full.log file
        with open(merged_log_file, 'w') as merged_file:
            merged_file.writelines(merged_log)
    except Exception as e:
        print(f"An error occurred while merging and sorting logs: {e}")