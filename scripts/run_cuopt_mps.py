#!/usr/bin/env python
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime


def resolve_executable(preferred: str | None) -> str:
    candidates = []
    if preferred:
        candidates.append(preferred)
    candidates.extend(["cuopt_cli", "cuopt"])  # common executable names
    for exe in candidates:
        path = shutil.which(exe)
        if path:
            return path
    raise FileNotFoundError(
        "cuOpt CLI executable not found. Tried: " + ", ".join(candidates) +
        ". Set --exe to the correct command or ensure it is on PATH."
    )


def build_command(exe: str, mps_path: str, time_limit: float | None, threads: int | None, extra: list[str]) -> list[str]:
    cmd = [exe, mps_path]
    # Add common flags if supported; many CLIs accept these, extra will allow full control.
    if time_limit is not None:
        cmd.extend(["--time-limit", str(time_limit)])
    if threads is not None:
        cmd.extend(["--threads", str(threads)])
    if extra:
        cmd.extend(extra)
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run NVIDIA cuOpt CLI on an MPS file")
    parser.add_argument("mps", help="Path to the .mps model file")
    parser.add_argument("--exe", help="cuOpt CLI executable name or path (default: auto-detect)")
    parser.add_argument("--time-limit", type=float, default=None, help="Time limit in seconds")
    parser.add_argument("--threads", type=int, default=None, help="Number of threads/workers")
    parser.add_argument("--log", default=None, help="Optional path to write full CLI output")
    parser.add_argument("--", dest="extra", nargs=argparse.REMAINDER, help="Extra flags forwarded to cuOpt CLI after --")

    args = parser.parse_args()

    mps_path = os.path.abspath(args.mps)
    if not os.path.exists(mps_path):
        print(f"ERROR: MPS file not found: {mps_path}")
        return 2

    try:
        exe_path = resolve_executable(args.exe)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 3

    extra = args.extra or []
    # Drop the leading "--" if present from argparse remainder
    if extra and extra[0] == "--":
        extra = extra[1:]

    cmd = build_command(exe_path, mps_path, args.time_limit, args.threads, extra)
    print("Running:", " ".join(cmd))

    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print(f"ERROR: Executable not found: {exe_path}")
        return 4

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    # Echo output to console
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)

    if args.log:
        log_path = os.path.abspath(args.log)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# cuOpt CLI run at {datetime.now().isoformat()}\n")
            f.write("# Command:\n")
            f.write(" ".join(cmd) + "\n\n")
            if stdout:
                f.write("# STDOUT\n")
                f.write(stdout)
                f.write("\n\n")
            if stderr:
                f.write("# STDERR\n")
                f.write(stderr)
                f.write("\n")
        print(f"Log written to {log_path}")

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())


