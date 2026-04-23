# Project Overview

This note records the current repository structure, the main workflows implemented by the project, and the problems found during a code-and-docs review.

## Purpose

This project converts external telemetry logs into MoTeC `.ld` files that can be opened in MoTeC i2. It supports three input types:

- Raw CAN bus logs recorded with `candump -l`
- Generic CSV logs
- COBB Accessport CSV logs

The generated `.ld` file is written through the `ldparser` submodule.

## Repository Structure

- `README.md`
  Main user-facing documentation, setup notes, and command examples.
- `motec_log_generator.py`
  Main CLI entry point. Validates arguments, loads the source log, dispatches parsing, and writes the MoTeC output file.
- `data_log.py`
  Normalization layer. Defines `DataLog`, `Channel`, and `Message`, and contains the format-specific parsers.
- `motec_log.py`
  MoTeC writer wrapper around `ldparser`. Builds metadata and channel payloads, then serializes the final `.ld` file.
- `replace_nulls_modify.py`
  In-place CSV cleanup utility that replaces empty cells with `0`.
- `replace_nulls.py`
  Non-destructive version of the same CSV cleanup utility. Writes a separate output file.
- `can_utils/`
  Small helper scripts for exploring CAN logs and generating a starter DBC.
- `examples/`
  Sample CAN, CSV, and Accessport inputs plus a sample DBC.
- `ldparser/`
  Git submodule used to pack MoTeC `.ld` binary structures.

## Core Workflow

### 1. Main conversion flow

1. A user runs `motec_log_generator.py` with a source file and a log type.
2. The script expands paths and validates the input files.
3. If the log type is `CSV`, the source file is modified in place to replace blank fields with `0`.
4. The source file is read into memory as lines.
5. A `DataLog` instance parses the source file into named telemetry channels.
6. A `MotecLog` instance is created and populated with MoTeC metadata such as driver, vehicle, venue, and event fields.
7. Each parsed channel is converted into the format expected by `ldparser`.
8. The final `.ld` file is written next to the source log unless `--output` is provided.

### 2. CAN log workflow

1. The user supplies a CAN dump and a DBC file.
2. `cantools` loads the DBC.
3. Each CAN frame line is parsed into timestamp, bus, arbitration ID, and payload bytes.
4. Only IDs present in the DBC are kept.
5. Each CAN frame is decoded into named signals using the DBC.
6. A `Channel` is created for each decoded signal and populated with timestamped values.
7. The channels are written into a MoTeC `.ld`.

### 3. Generic CSV workflow

1. The first column is treated as time.
2. Each remaining column becomes a telemetry channel.
3. Each row is converted into timestamped numeric samples.
4. Channels containing non-numeric values are dropped.
5. The remaining channels are written into a MoTeC `.ld`.

Note: the intended workflow described above matches the README, but the current implementation has important caveats listed in the Problems section.

### 4. Accessport workflow

1. The Accessport CSV is parsed through the generic CSV parser.
2. The `AP Info` column is removed.
3. Headers of the form `Name (Units)` are split into channel name and units.
4. The resulting channels are written into a MoTeC `.ld`.

### 5. CAN utility workflows

- `can_utils/list_can_ids.py`
  Reads a CAN log and prints each unique CAN ID with a message count.
- `can_utils/list_can_messages.py`
  Filters a CAN log to one ID and prints the raw payload bytes over time.
- `can_utils/dbc_file_from_can_log.py`
  Scans a CAN log and generates a starter DBC where each observed byte becomes its own 8-bit signal.

## Implementation Notes

- The project uses a common in-memory representation of telemetry before writing the MoTeC file.
- `Channel.avg_frequency()` computes a frequency from message count and duration, and that value is written into the MoTeC metadata for each channel.
- `motec_log.py` currently forces channel decimals to `0` because of a limitation noted in `ldparser` handling.
- The MoTeC writer uses hard-coded file pointer offsets that were derived from inspecting existing `.ld` files.

## Problems Found

### 1. Resampling is documented but currently disabled

The README says all signals are resampled to a fixed frequency and exposes a `--frequency` option for that purpose. In the current code, the actual resampling call in `motec_log_generator.py` is commented out.

Impact:

- `--frequency` does not currently resample the data.
- Channels may keep irregular source spacing while still being written with only an average frequency value.
- This is the biggest mismatch between the documented workflow and the code.

### 2. Generic CSV parsing does not match the README or sample CSV

The README says generic CSV input needs time in the first column and that channels will not have units. The current parser in `data_log.py` assumes:

- Row 1 is headers
- Row 2 is a units row
- Data starts on row 3

Impact:

- A normal header-plus-data CSV will have its first data row treated as units and skipped.
- The sample file in `examples/csv_sample.csv` does not include a units row, so the implementation does not match the example data shape.
- The code also stores units for generic CSV input even though the README says generic CSV channels have no units.

### 3. Accessport parsing inherits the CSV row-shape problem

`from_accessport_log()` calls the generic CSV parser first and then cleans up Accessport-specific headers.

Impact:

- The first real data row is effectively consumed as a units row before the Accessport-specific cleanup happens.
- Accessport logs may therefore lose their first sample.
- This is another docs-versus-code mismatch because the README presents Accessport logs as directly supported.

### 4. CAN ID counting in `can_utils` is off by one

`can_utils.can_ids_from_lines()` initializes a newly seen CAN ID with:

- `msgs = 0`
- `bytes = 0`

instead of recording the first observed frame immediately.

Impact:

- `list_can_ids.py` undercounts every CAN ID by one message.
- `dbc_file_from_can_log.py` can generate a zero-byte message definition for an ID that appears only once.
- Byte-length discovery for rare IDs is unreliable.

### 5. Documentation typo in the examples README

`examples/README.md` lists `accessport_sample.log` under the Accessport example, but the actual sample file in the repository is `accessport_sample.csv`.

Impact:

- Small but confusing paper cut for anyone using the bundled examples.

### 6. CSV null replacement is inconsistent across input types

The main script replaces empty cells with `0` only for the `CSV` path, not for the `ACCESSPORT` path.

Impact:

- Generic CSV input gets preprocessing for blanks.
- Accessport input does not get the same cleanup and may drop channels if blank values appear.
- This is not necessarily a bug for all logs, but it is inconsistent behavior.

## Recommended Follow-Up Fixes

1. Decide whether resampling should be enabled again or removed from the documented behavior.
2. Update `from_csv_log()` so it supports the actual documented format: header row plus data rows, with units either absent or optional.
3. Update `from_accessport_log()` after the CSV parser change so Accessport files do not lose the first sample.
4. Fix `can_utils.can_ids_from_lines()` so first-seen IDs record both message count and payload length correctly.
5. Correct the example filename in `examples/README.md`.
6. Decide whether blank-value preprocessing should also apply to Accessport logs.

## Review Scope

This note is based on a direct review of the repository docs and source files. A full runtime verification was limited because the current environment did not have the Python dependency `cantools` available during review.
