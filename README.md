# MotecLogGenerator

Utility for generating MoTeC .ld files that can be analyzed with [i2 Pro](https://www.motec.com.au/i2/i2overview/) from external log sources. Generated log files are "Pro Enabled", so they can be opened in either *i2 Standard* or *i2 Pro*.

Currently the following input types are supported:
* Raw CAN bus logs (see logging instructions below)
* CSV files
* [COBB Accessport](https://www.cobbtuning.com/products/accessport) logs

CAN bus logs must be paired with a [DBC](https://docs.openvehicles.com/en/latest/components/vehicle_dbc/docs/dbc-primer.html) file describing the structure of the frames.

*Tip:* To clone with the submodule included run:
```bash
git clone --recursive git@github.com:stevendaniluk/MotecLogGenerator.git
```

## Quick Start
From the repository root:

1. Install dependencies:

```bash
pip install cantools numpy pandas
```

2. Convert one of the sample inputs:

CAN:
```bash
python3 motec_log_generator.py examples/can_sample.log CAN --dbc examples/sample_can_spec.dbc
```

CSV:
```bash
python3 motec_log_generator.py examples/csv_sample.csv CSV
```

Accessport:
```bash
python3 motec_log_generator.py examples/accessport_sample.csv ACCESSPORT
```

3. Find the generated `.ld` file next to the input file unless you passed `--output`.

For the larger real-world CSV currently included in `examples/`, you can run:

```bash
python3 motec_log_generator.py examples/4-18-tire-scrub-stint2.csv CSV
```

## Repository Layout
The top-level directory is organized like this:

* `motec_log_generator.py`
  Main CLI entry point for converting input logs into `.ld` files.
* `data_log.py`
  Input parsing and normalization layer for CAN, CSV, and Accessport data.
* `motec_log.py`
  Writer that converts normalized channel data into MoTeC `.ld` output.
* `examples/`
  Example input files you can run directly against the converter.
* `can_utils/`
  Helper scripts for inspecting CAN logs and generating a starter DBC.
* `tools/`
  Local profiling and benchmarking helpers used during performance work.
* `ldparser/`
  Bundled parser/writer dependency used for MoTeC `.ld` structures.

## How Paths And Directories Work
Run commands from the repository root unless noted otherwise.

* The `log` argument can be either a relative path or an absolute path.
* If you do not pass `--output`, the generated `.ld` file is written next to the input file with the same base name.
* If you do pass `--output`, the tool writes to that path instead and will create the destination directory if needed.

Examples:

* Input `examples/csv_sample.csv` with no `--output` produces `examples/csv_sample.ld`
* Input `C:\data\session.csv` with no `--output` produces `C:\data\session.ld`
* Input `examples/csv_sample.csv --output out\session.ld` produces `out\session.ld`

## Usage
Check out the `examples/` directory for sample log files you can use to test the tool.

### CAN Bus Logs
```bash
python3 motec_log_generator.py /path/to/my/data/can_data.log CAN --dbc /path/to/my/data/car.dbc
```

This will generate a motec .ld file `/path/to/my/data/can_data.ld`.

### CSV Logs
```bash
python3 motec_log_generator.py /path/to/my/data/csv_data.csv CSV
```

This will generate a motec .ld file `/path/to/my/data/csv_data.ld`.

CSV behavior:

* The first column must be time.
* A second row of units is optional.
* If a units row is present, those units are copied into the generated MoTeC channels.
* If no units row is present, channels are created with empty units.
* Blank CSV cells are treated as `0`.
* Duplicate header names are kept by adding suffixes like `_2`, `_3`, and so on.

This means both of the following CSV layouts are supported:

```csv
Time,RPM,Speed
0.00,1000,0
0.01,1010,0
```

```csv
Time,RPM,Speed
s,rpm,km/h
0.00,1000,0
0.01,1010,0
```

### Accessport Logs

```bash
python3 motec_log_generator.py /path/to/my/data/accessport_data.csv ACCESSPORT
```

This will generate a motec .ld file `/path/to/my/data/accessport_data.ld`.

### Additional Options
A different destination and filename for the generated .ld file can also be specified by adding the following to the command:
```bash
--output /path/to/different/location/new_filename.ld
```

It is also possible to provide additional arguments to populate the metadata in the motec log file for driver, venue, vehicle, etc. See the usage below for full details.

Note on `--frequency`:

* The CLI still accepts `--frequency`, but resampling is currently disabled in the main conversion path.
* Channel frequency metadata is still derived from the observed sample timing in the parsed data.

```
usage: motec_log_generator.py [-h] [--output OUTPUT] [--frequency FREQUENCY]
                              [--dbc DBC] [--driver DRIVER]
                              [--vehicle_id VEHICLE_ID]
                              [--vehicle_weight VEHICLE_WEIGHT]
                              [--vehicle_type VEHICLE_TYPE]
                              [--vehicle_comment VEHICLE_COMMENT]
                              [--venue_name VENUE_NAME]
                              [--event_name EVENT_NAME]
                              [--event_session EVENT_SESSION]
                              [--long_comment LONG_COMMENT]
                              [--short_comment SHORT_COMMENT]
                              log {CAN,CSV,ACCESSPORT}

Generates MoTeC .ld files from external log files generated by: CAN bus dumps,
CSV files, or COBB Accessport CSV files

positional arguments:
  log                   Path to logfile
  {CAN,CSV,ACCESSPORT}  Type of log to process

options:
  -h, --help            show this help message and exit
  --output OUTPUT       Name of output file, defaults to same as 'candump'
  --frequency FREQUENCY
                        Fixed frequency to resample all channels at
  --dbc DBC             Path to DBC file, required if log type CAN
  --driver DRIVER       Motec log metadata field
  --vehicle_id VEHICLE_ID
                        Motec log metadata field
  --vehicle_weight VEHICLE_WEIGHT
                        Motec log metadata field
  --vehicle_type VEHICLE_TYPE
                        Motec log metadata field
  --vehicle_comment VEHICLE_COMMENT
                        Motec log metadata field
  --venue_name VENUE_NAME
                        Motec log metadata field
  --event_name EVENT_NAME
                        Motec log metadata field
  --event_session EVENT_SESSION
                        Motec log metadata field
  --long_comment LONG_COMMENT
                        Motec log metadata field
  --short_comment SHORT_COMMENT
                        Motec log metadata field

The CAN bus log must be the same format as what is generated by 'candump' with
the '-l' option from the linux package can-utils. A MoTeC channel will be
created for every signal in the DBC file that has messages in the CAN log. The
signal name and units will be directly copied from the DBC file. CSV files
must have time as their first column. A MoTeC channel will be generated for
all remaining columns. If a second row of units is present it will be copied
into the generated channels. COBB Accessport CSV logs are simply generated by
starting a logging session on the accessport. A MoTeC channel will be created
for every channel logged, the name and units will be directly copied over.
```

## Generating CAN Logs

On a linux machine connected to the CAN bus you can run:
```bash
candump can0 -l > my_candump.log
```

It will generate a log file formatted like below:
```
(1630268615.800257) can0 0D4#0000000000000000
(1630268615.801277) can0 152#E9BC00000000008C
(1630268615.802316) can0 380#150A00000000001F
(1630268615.807716) can0 140#0082C34300000981
(1630268615.808638) can0 141#6A263B27C4C32103
...
```

## CAN Utilities
Under the `can_utils` directory there are some tools for:
* Inspecting the CAN Id's contained in a log file
* Inspecting the messages from a particular Id in a CAN log
* Generating a DBC file with signals for individual bytes from every Id present

## Dependencies
* Python 3
* [cantools](https://cantools.readthedocs.io)
* [numpy](https://numpy.org/)
* [pandas](https://pandas.pydata.org/) (optional but recommended for much faster CSV and Accessport imports)

```bash
pip install cantools numpy pandas
```

## Disclaimer
This work was produced for research purposes. It should in no way be used to circumvent MoTeC's licensing requirements for their data loggers or i2 analysis software.
