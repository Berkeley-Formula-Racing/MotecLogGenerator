#!/usr/bin/env python3

import argparse
import os
import sys
import time
import tracemalloc

import cantools

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from data_log import DataLog
from motec_log import MotecLog


def mib(nbytes):
    return nbytes / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(
        description="Profile CAN log conversion by timing the major pipeline stages."
    )
    parser.add_argument("log", help="Path to the CAN log")
    parser.add_argument("--dbc", required=True, help="Path to the DBC file")
    parser.add_argument("--output", required=True, help="Path to the output .ld file")
    parser.add_argument(
        "--tracemalloc",
        action="store_true",
        help="Enable Python allocation tracking for rough peak-memory reporting",
    )
    args = parser.parse_args()

    log_path = os.path.expanduser(args.log)
    dbc_path = os.path.expanduser(args.dbc)
    output_path = os.path.expanduser(args.output)

    if args.tracemalloc:
        tracemalloc.start()

    phase_timings = {}

    t0 = time.perf_counter()
    with open(log_path, "r") as f:
        lines = f.readlines()
    phase_timings["read_log"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    can_db = cantools.database.load_file(dbc_path)
    phase_timings["load_dbc"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    data_log = DataLog()
    data_log.from_can_log(lines, can_db)
    phase_timings["decode_can"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    motec_log = MotecLog()
    motec_log.initialize()
    motec_log.add_all_channels(data_log)
    phase_timings["build_ld_channels"] = time.perf_counter() - t0

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    t0 = time.perf_counter()
    motec_log.write(output_path)
    phase_timings["write_ld"] = time.perf_counter() - t0

    total_time = sum(phase_timings.values())
    log_size = os.path.getsize(log_path)
    output_size = os.path.getsize(output_path) if os.path.isfile(output_path) else 0
    total_messages = sum(channel.sample_count() for channel in data_log.channels.values())

    print(f"log: {log_path}")
    print(f"log_size_mib: {mib(log_size):.2f}")
    print(f"channels: {len(data_log.channels)}")
    print(f"channel_samples: {total_messages}")
    print(f"output_size_mib: {mib(output_size):.2f}")
    print(f"total_time_s: {total_time:.3f}")
    print(f"throughput_mib_per_s: {mib(log_size) / total_time:.2f}")
    for name, seconds in phase_timings.items():
        percent = 100.0 * seconds / total_time if total_time else 0.0
        print(f"{name}_s: {seconds:.3f} ({percent:.1f}%)")

    if args.tracemalloc:
        current, peak = tracemalloc.get_traced_memory()
        print(f"python_alloc_current_mib: {mib(current):.2f}")
        print(f"python_alloc_peak_mib: {mib(peak):.2f}")


if __name__ == "__main__":
    main()
