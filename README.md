# Motec Log Generator (C Version)

This project is a C implementation of the original Python-based Motec Log Generator. The C version is intended to replicate the functionality of the Python version while improving performance.

## Known Issues
- **CSV Parsing:**
  - For the `0013.csv` file:
    - **Python Version (Original):** Parses 290 columns.
    - **C Version:** Parses 294 columns.

While 294 lines matches up with the actual amount of columns in the csv, the descrepancy could be causing the issue. There are similar discrepancies are  with other CSV files, where the Python version parses fewer lines than the C version. This might not be behind the `.ld file cannot open` error, but it's something to take note of.
    
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
