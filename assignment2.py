#!/usr/bin/env python3

'''
OPS445 Assignment 2 - Summer 2026
Program: assignment2.py 
Author: "Ambika Kumari Koiri"
Student ID: "Akkoiri"
The python code in this file is original work written by
"Ambika Kumari Koiri". No code in this file is copied from any other source 
except those provided by the course instructor, including any person, 
textbook, or on-line resource. I have not shared this python script 
with anyone or anything except for submission for grading.  
I understand that the Academic Honesty Policy will be enforced and 
violators will be reported and appropriate action will be taken.

Description: Memory Usage Visualizer – displays total system memory usage 
             or per‑process memory for a given program.

Date: 2026-07-17
'''

import argparse
import os
import sys

def parse_command_args() -> object:
    "Set up argparse here. Call this function inside main."
    parser = argparse.ArgumentParser(
        description="Memory Visualiser -- See Memory Usage Report with bar charts",
        epilog="Copyright 2023"
    )
    parser.add_argument(
        "-l", "--length", type=int, default=20,
        help="Specify the length of the graph. Default is 20."
    )
    parser.add_argument(
        "-H", "--human-readable",
        action="store_true",
        help="Prints sizes in human readable format"
    )
    parser.add_argument(
        "program", type=str, nargs='?',
        help="if a program is specified, show memory use of all associated processes. Show only total use if not."
    )
    args = parser.parse_args()
    return args

def percent_to_graph(percent: float, length: int = 20) -> str:
    """
    Convert a percentage (0.0 to 1.0) into a bar graph string.
    The graph consists of '#' for filled portion and spaces for the rest.
    The total length is fixed to `length`.
    """
    hash_count = int(round(percent * length))
    hash_count = min(hash_count, length)
    graph = '#' * hash_count + ' ' * (length - hash_count)
    return graph

def get_sys_mem() -> int:
    """
    Return total system memory in KiB by reading /proc/meminfo.
    """
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1])
    except FileNotFoundError:
        print("Error: /proc/meminfo not found", file=sys.stderr)
        sys.exit(1)
    return 0

def get_avail_mem() -> int:
    """
    Return available memory in KiB by reading /proc/meminfo.
    For WSL systems where MemAvailable is not present, fall back to MemFree + SwapFree.
    """
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    value = int(parts[1])
                    meminfo[key] = value

            if 'MemAvailable' in meminfo:
                return meminfo['MemAvailable']
            else:
                # WSL fallback
                return meminfo.get('MemFree', 0) + meminfo.get('SwapFree', 0)
    except FileNotFoundError:
        print("Error: /proc/meminfo not found", file=sys.stderr)
        sys.exit(1)
    return 0

def pids_of_prog(app_name: str) -> list:
    """Return all PIDs associated with a program."""
    output = os.popen("pidof " + app_name).read()
    return output.split()

def rss_mem_of_pid(proc_id: str) -> int:
    """
    Given a process id, return the Resident memory used by reading /proc/<pid>/smaps.
    Sums all lines starting with 'Rss:' to get total RSS in KiB.
    """
    try:
        smaps_path = f'/proc/{proc_id}/smaps'
        total_rss = 0
        with open(smaps_path, 'r') as f:
            for line in f:
                if line.startswith('Rss:'):
                    total_rss += int(line.split()[1])
        return total_rss
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return 0

def bytes_to_human_r(kibibytes: int, decimal_places: int = 2) -> str:
    "turn 1,024 into 1 MiB, for example"
    suffixes = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    suf_count = 0
    result = kibibytes
    while result > 1024 and suf_count < len(suffixes) - 1:
        result /= 1024
        suf_count += 1
    str_result = f'{result:.{decimal_places}f} '
    str_result += suffixes[suf_count]
    return str_result

if __name__ == "__main__":
    args = parse_command_args()

    total_mem = get_sys_mem()
    avail_mem = get_avail_mem()
    used_mem = total_mem - avail_mem
    usage_percent = used_mem / total_mem if total_mem > 0 else 0

    if not args.program:
        graph = percent_to_graph(usage_percent, args.length)
        if args.human_readable:
            used_str = bytes_to_human_r(used_mem)
            total_str = bytes_to_human_r(total_mem)
        else:
            used_str = str(used_mem)
            total_str = str(total_mem)
        percent_display = int(usage_percent * 100)
        print(f"Memory         [{graph} | {percent_display}%] {used_str}/{total_str}")
    else:
        pids = pids_of_prog(args.program)
        if not pids:
            print(f"{args.program} not found.")
            sys.exit(1)

        process_data = []
        total_rss = 0
        for pid in pids:
            rss = rss_mem_of_pid(pid)
            process_data.append((pid, rss))
            total_rss += rss

        process_data.sort(key=lambda x: x[1], reverse=True)

        for pid, rss in process_data:
            mem_percent = rss / total_mem if total_mem > 0 else 0
            graph = percent_to_graph(mem_percent, args.length)
            if args.human_readable:
                mem_str = bytes_to_human_r(rss)
                total_str = bytes_to_human_r(total_mem)
            else:
                mem_str = str(rss)
                total_str = str(total_mem)
            percent_display = int(mem_percent * 100)
            print(f"{pid:<12} [{graph} | {percent_display}%] {mem_str}/{total_str}")

        if len(process_data) > 1:
            mem_percent = total_rss / total_mem if total_mem > 0 else 0
            graph = percent_to_graph(mem_percent, args.length)
            if args.human_readable:
                mem_str = bytes_to_human_r(total_rss)
                total_str = bytes_to_human_r(total_mem)
            else:
                mem_str = str(total_rss)
                total_str = str(total_mem)
            percent_display = int(mem_percent * 100)
            print(f"{args.program:<12} [{graph} | {percent_display}%] {mem_str}/{total_str}")
