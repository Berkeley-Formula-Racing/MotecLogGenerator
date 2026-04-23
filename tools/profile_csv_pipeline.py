#!/usr/bin/env python3

import argparse
import os
import shutil
import sys
import time
import tracemalloc

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from data_log import DataLog
from motec_log import MotecLog
from replace_nulls_modify import replace_nulls


def mib(nbytes):
    return nbytes / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(
        description="Profile CSV log conversion by timing the major pipeline stages."
    )
    parser.add_argument("log", help="Path to the CSV log")
    parser.add_argument("--output", required=True, help="Path to the output .ld file")
    parser.add_argument(
        "--work-copy",
        help="Optional path to a writable copy used for the in-place null-replacement step",
    )
    parser.add_argument(
        "--replace-nulls",
        action="store_true",
        help="Include the legacy in-place null-replacement preprocessing step in the profile",
    )
    parser.add_argument(
        "--tracemalloc",
        action="store_true",
        help="Enable Python allocation tracking for rough peak-memory reporting",
    )
    args = parser.parse_args()

    log_path = os.path.expanduser(args.log)
    output_path = os.path.expanduser(args.output)
    work_copy_path = os.path.expanduser(args.work_copy) if args.work_copy else log_path

    if args.work_copy:
        shutil.copy2(log_path, work_copy_path)
        os.chmod(work_copy_path, 0o666)

    if args.tracemalloc:
        tracemalloc.start()

    phase_timings = {}

    if args.replace_nulls:
        t0 = time.perf_counter()
        replace_nulls(work_copy_path)
        phase_timings["replace_nulls"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    data_log = DataLog()
    with open(work_copy_path, "r", newline="") as f:
        data_log.from_csv_log(f)
    phase_timings["parse_csv"] = time.perf_counter() - t0

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
    log_size = os.path.getsize(work_copy_path)
    output_size = os.path.getsize(output_path) if os.path.isfile(output_path) else 0
    total_messages = sum(channel.sample_count() for channel in data_log.channels.values())

    print(f"log: {log_path}")
    print(f"work_copy: {work_copy_path}")
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
