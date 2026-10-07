# Conversion memory and performance

CSV ingestion accepts file paths and streams without loading all input lines or making
a Message object for every CSV sample. Units, duplicates and missing-value handling
match the installed CANary converter. Files up to 128 MiB use the float32 pandas path;
larger files use chunked parsing and a temporary disk-backed matrix. Override this
threshold with `CANARY_CSV_MEMORY_LIMIT_MB` (0 forces disk-backed conversion).

MotecLog retains channel source views and ldparser scales/writes blocks. CSV channels
keep the installed converter's three decimal places using rounded int32 storage.
The general ldparser read/write paths remain available.

Regression on 329 channels and 50,611 samples produced identical decoded values and
channel metadata to the installed converter. Local fast-mode timings were 0.85 vs 1.42 s;
forced memory mode reduced peak RAM from about 209 to 143 MiB but took about 2.1 s.
