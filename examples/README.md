# MotecLogGenerator Examples

This directory contains some sample files to use with the MoTeC log generator tool.

When you run the commands below from inside `examples/`, the generated `.ld` file is written into the same directory unless you pass `--output`.

## CAN
Files:
* `can_sample.log`
* `sample_can_spec.dbc`

Usage:
```bash
python3 ../motec_log_generator.py can_sample.log CAN --dbc sample_can_spec.dbc
```

## CSV
Files:
* `csv_sample.csv`

Usage:
```bash
python3 ../motec_log_generator.py csv_sample.csv CSV
```

This sample uses a simple CSV layout with a header row followed directly by data rows.

## Accessport
Files:
* `accessport_sample.csv`

Usage:
```bash
python3 ../motec_log_generator.py accessport_sample.csv ACCESSPORT
```
