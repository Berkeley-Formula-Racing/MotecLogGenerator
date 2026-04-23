#!/usr/bin/env python3

import argparse
import os


def parse_line(line):
    stamp, bus, msg = line.split()
    frame_id, data = msg.split("#")
    return float(stamp[1:-1]), bus, frame_id, data


def format_line(stamp, bus, frame_id, data):
    return f"({stamp:.6f}) {bus} {frame_id}#{data}\n"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a larger synthetic candump log by repeating a source log with timestamp offsets."
    )
    parser.add_argument("input_log", help="Path to a source candump log")
    parser.add_argument("output_log", help="Path to the generated output log")
    parser.add_argument(
        "--target-mb",
        type=float,
        default=90.0,
        help="Approximate target file size in MiB for the generated log",
    )
    parser.add_argument(
        "--gap-seconds",
        type=float,
        default=0.001,
        help="Gap to insert between repeated source-log blocks",
    )
    args = parser.parse_args()

    input_log = os.path.expanduser(args.input_log)
    output_log = os.path.expanduser(args.output_log)

    if not os.path.isfile(input_log):
        raise SystemExit(f"ERROR: input log does not exist: {input_log}")

    with open(input_log, "r", newline="") as f:
        lines = f.readlines()

    if not lines:
        raise SystemExit("ERROR: input log is empty")

    parsed = [parse_line(line) for line in lines]
    start_stamp = parsed[0][0]
    end_stamp = parsed[-1][0]
    source_duration = max(0.0, end_stamp - start_stamp)
    block_span = source_duration + args.gap_seconds

    source_size = os.path.getsize(input_log)
    target_size = int(args.target_mb * 1024 * 1024)
    repeat_count = max(1, (target_size + source_size - 1) // source_size)

    output_dir = os.path.dirname(output_log)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_log, "w", newline="") as out:
        for block_index in range(repeat_count):
            time_offset = block_index * block_span
            for stamp, bus, frame_id, data in parsed:
                shifted_stamp = (stamp - start_stamp) + time_offset
                out.write(format_line(shifted_stamp, bus, frame_id, data))

    output_size = os.path.getsize(output_log)
    print(f"Generated {output_log}")
    print(f"Source size: {source_size / (1024 * 1024):.2f} MiB")
    print(f"Output size: {output_size / (1024 * 1024):.2f} MiB")
    print(f"Repeats: {repeat_count}")
    print(f"Block span: {block_span:.6f} s")


if __name__ == "__main__":
    main()
