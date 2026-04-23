# Performance Debugging Tasks

This checklist tracks the current performance investigation for large log processing.

## Current Branch

- `optimize-csv-pass1`

## Goal

Improve throughput and responsiveness when converting large log files, with enough visibility to tell whether time is being spent in file I/O, parsing, CAN decoding, in-memory data representation, or `.ld` writing.

## Investigation Tasks

- [x] Baseline runtime on the bundled sample CAN log.
- [x] Baseline runtime on the bundled sample CSV and Accessport logs.
- [x] Create a repeatable large benchmark log in the workspace for performance testing.
- [x] Measure total runtime on the large benchmark log.
- [x] Separate parse/decode time from `.ld` serialization time.
- [x] Add coarse progress reporting during long-running phases.
- [x] Identify avoidable full-file reads and duplicate passes over input data.
- [x] Identify avoidable Python object allocation and data-copy hotspots.
- [x] Determine whether `cantools` decode is the main bottleneck or only a secondary one.
- [x] Decide whether optimization should stay in Python or justify moving part of the pipeline to another implementation.

## Likely Work Items

- [x] Stream input instead of using `readlines()`.
- [ ] Cache DBC message lookups by frame ID.
- [x] Replace per-sample Python `Message` objects with a lower-overhead representation.
- [ ] Avoid unnecessary full-data copies before writing `.ld` output.
- [x] Remove the separate CSV null-replacement preprocessing pass or fold it into parsing.
- [x] Add benchmark notes and results to the repository.

## Current Results

- Baseline CAN sample: about `1.0s` for `examples/can_sample.log` copied into `bench/`.
- Baseline CSV sample: about `0.57s`.
- Baseline Accessport sample: about `0.68s`.
- Real CSV workload: `examples/4-18-tire-scrub-stint2.csv`
  - size: about `44.86 MiB`
  - columns: `301`
  - data rows: `58,763`
- Large synthetic CAN benchmark: `bench/can_benchmark_90mb.log`, approximately `79.23 MiB`.
- Large benchmark total runtime: about `6.4s` through the main script on this machine.
- Phase timing on the large benchmark using `tools/profile_can_pipeline.py`:
  - `read_log`: about `0.29s` (`5.2%`)
  - `load_dbc`: about `0.02s` (`0.3%`)
  - `decode_can`: about `4.22s` (`77.0%`)
  - `build_ld_channels`: about `0.96s` (`17.4%`)
  - `write_ld`: about `0.005s` (`0.1%`)
- Real CSV runtime through the current main script on a writable bench copy: about `28.4s`
- Phase timing on the real CSV using `tools/profile_csv_pipeline.py`:
  - `replace_nulls`: about `1.78s` (`8.0%`)
  - `read_log`: about `0.15s` (`0.7%`)
  - `parse_csv`: about `13.12s` (`58.7%`)
  - `build_ld_channels`: about `7.28s` (`32.6%`)
  - `write_ld`: about `0.03s` (`0.1%`)
- Post-patch real CSV runtime through the main script on the original input: about `21.6s`
- Post-patch phase timing on the real CSV using `tools/profile_csv_pipeline.py`:
  - `read_log`: about `0.15s` (`0.9%`)
  - `parse_csv`: about `12.14s` (`75.4%`)
  - `build_ld_channels`: about `3.79s` (`23.5%`)
  - `write_ld`: about `0.03s` (`0.2%`)
- Fresh branch baseline on `optimize-csv-pass1`:
  - main script runtime on `examples/4-18-tire-scrub-stint2.csv`: about `25.5s`
  - phase timing:
    - `read_log`: about `0.15s` (`0.8%`)
    - `parse_csv`: about `15.01s` (`77.7%`)
    - `build_ld_channels`: about `4.12s` (`21.3%`)
    - `write_ld`: about `0.03s` (`0.2%`)
  - tracemalloc peak Python allocations: about `2228 MiB`
- Current optimized results on `optimize-csv-pass1`:
  - main script runtime on `examples/4-18-tire-scrub-stint2.csv`: about `5.0s`
  - phase timing:
    - `read_log`: about `0.15s` (`3.7%`)
    - `parse_csv`: about `3.07s` (`74.2%`)
    - `build_ld_channels`: about `0.88s` (`21.3%`)
    - `write_ld`: about `0.03s` (`0.7%`)
  - tracemalloc peak Python allocations: about `664 MiB`
- Current pandas-backed results on `optimize-csv-pass1`:
  - main script runtime on `examples/4-18-tire-scrub-stint2.csv`: about `1.14s`
  - phase timing:
    - `parse_csv`: about `0.45s`
    - `build_ld_channels`: about `0.002s`
    - `write_ld`: about `0.03s`
  - tracemalloc peak Python allocations: about `135 MiB`

## Current Conclusions

- The program feels unresponsive mostly because it emits no progress during the long CAN decode phase, not because `.ld` writing is slow.
- `cantools` decoding is a major bottleneck, but it is not the whole story.
- The current in-memory method also costs a meaningful amount of time:
  - per-line string parsing
  - creating millions of `Message` objects
  - appending into Python lists
  - copying all channel values again into NumPy arrays before writing
- The `.ld` write itself is almost free compared with the parse and channel-build stages.
- A Python rewrite of the pipeline structure is still the best first move before considering another language.
- For the real CSV workload, the dominant costs are:
  - the extra in-place null-replacement pass
  - per-cell string splitting and float conversion
  - creating millions of `Message` objects
  - copying all values again into NumPy arrays before `.ld` output

## Real CSV Findings

- The actual target file shape matches the current CSV parser better than the small sample CSV because it includes both:
  - a header row
  - a units row
- The current CSV path assumes it can rewrite the source file in place before parsing.
  - This was fixed by folding blank-cell handling into CSV parsing instead of rewriting the input.
- The current parser uses naive `str.split(',')` on raw lines instead of `csv.reader`.
  - This was fixed by switching CSV parsing to `csv.reader`.
- The real CSV contains one duplicate channel name: `FuelCutState`.
  - This was fixed by preserving duplicates with numbered suffixes such as `FuelCutState_2`.
  - The converter now produces `300` channels instead of `299`.

## Next Pass Focus

- Decide whether the optional pandas fast path should become the documented preferred path or remain an opportunistic accelerator.
- Consider restoring percentage-based progress reporting for the pandas path if user experience matters more than minimal overhead.
- Revisit the CAN path with the same discipline now that the CSV path is much cheaper.

## Change Log

- Created a local git branch for the current optimization pass: `optimize-csv-pass1`.
- Re-validated the real CSV workload before further edits.
- Recorded a fresh runtime and memory baseline for the next optimization step.
- Refactored the CSV/Accessport path to stream rows instead of reading the whole file into `lines`.
- Removed CSV `Message` object creation in favor of one shared timestamp list plus per-channel value buffers.
- Updated the MoTeC writer to consume channel values through a generic iterator interface.
- Verified that the real CSV, sample CAN log, and sample Accessport log still convert successfully.
- Measured the latest real-CSV improvement from about `25.5s` to about `5.0s` and from about `2228 MiB` peak Python allocations to about `664 MiB`.
- Added an optional pandas-backed fast path for file-based CSV and Accessport inputs.
- Reused NumPy-backed channel arrays directly in the MoTeC writer to avoid another per-channel copy.
- Re-profiled the real CSV after the pandas path:
  - about `1.14s` through the main script
  - about `0.60s` in the instrumented pipeline with tracemalloc
  - about `135 MiB` peak Python allocations
- Updated `README.md` and `examples/README.md` to document:
  - current CSV behavior
  - path and output-directory behavior
  - repository layout
  - corrected example filenames
- Added a short Quick Start section to `README.md` with install commands, sample conversions, and the default output-location behavior.
