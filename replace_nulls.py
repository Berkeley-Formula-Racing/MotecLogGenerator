#!/usr/bin/env python3
import csv
import argparse
import os

def replace_nulls(input_file, output_file):
    with open(input_file, 'r', newline='') as csv_in, open(output_file, 'w', newline='') as csv_out:
        reader = csv.reader(csv_in)
        writer = csv.writer(csv_out)
        for row in reader:
            # Replace any field that is empty or only whitespace with "0"
            new_row = [ "0" if field.strip() == "" else field for field in row ]
            writer.writerow(new_row)

def main():
    parser = argparse.ArgumentParser(
        description="Replace null (empty) values in a CSV file with 0."
    )
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument("--output", help="Path for the output CSV file (default: input filename with '_no_nulls' appended)", default=None)

    args = parser.parse_args()
    input_file = os.path.expanduser(args.csv_file)
    
    if not os.path.isfile(input_file):
        print(f"ERROR: CSV file '{input_file}' does not exist.")
        exit(1)

    # If no output file name provided, create one based on the input filename.
    if args.output:
        output_file = os.path.expanduser(args.output)
    else:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_no_nulls{ext}"

    replace_nulls(input_file, output_file)
    print(f"Processed CSV file saved as: {output_file}")

if __name__ == '__main__':
    main()