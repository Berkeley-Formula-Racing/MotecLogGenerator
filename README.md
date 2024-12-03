# Motec Log Generator (C Version)

This project is a C implementation of the original Python-based Motec Log Generator. The C version is intended to replicate the functionality of the Python version while improving performance.

## Known Issues
- **CSV Parsing:** There appears to be an issue with parsing the inputted CSV file. For example, when tested with the 0013.csv file:
  - Expected behavior: The software should parse 294 columns.
  - Current behavior: Only 44 columns are being parsed.
  - This may be the cause of the `".ld file cannot open"` error when I try to open the generated `.ld` file with the Motec software.
  - There are similar issue with other csv files - not all of the columns are getting parsed.

## Usage

### Compilation
Compile the program using the following command:
```bash
gcc -o motec_log_generator motec_log_generator.c data_log.c motec_log.c ldparser.c -lm 
```

Run the program with:
```
./motec_log_generator <csv_file_path> CSV
```
