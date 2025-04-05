#!/usr/bin/env python3
import csv
import argparse
import os

def replace_nulls(input_file):
    # Read the entire file into memory.
    with open(input_file, 'r', newline='') as csv_in:
        reader = csv.reader(csv_in)
        rows = list(reader)
    
    # Write the processed data back into the same file.
    with open(input_file, 'w', newline='') as csv_out:
        writer = csv.writer(csv_out)
        for row in rows:
            # Replace any field that is empty or only whitespace with "0"
            new_row = ["0" if field.strip() == "" else field for field in row]
            writer.writerow(new_row)

def main():
    parser = argparse.ArgumentParser(
        description="Replace null (empty) values in a CSV file with 0 by modifying the file in place."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to modify")
    args = parser.parse_args()
    
    input_file = os.path.expanduser(args.csv_file)
    
    if not os.path.isfile(input_file):
        print(f"ERROR: CSV file '{input_file}' does not exist.")
        exit(1)
    
    replace_nulls(input_file)
    print(f"CSV file '{input_file}' has been modified successfully.")

if __name__ == '__main__':
    main()