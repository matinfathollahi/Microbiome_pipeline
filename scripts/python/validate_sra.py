#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import subprocess
import sys

if len(sys.argv) != 3:
    sys.exit("Usage: validate_sra.py <input.sra> <output.ok>")

sra_file = Path(sys.argv[1])
ok_file = Path(sys.argv[2])

if not sra_file.exists():
    raise FileNotFoundError(f"{sra_file} not found.")

if sra_file.stat().st_size == 0:
    raise ValueError(f"{sra_file} is empty.")

try:
    result = subprocess.run(
        ["vdb-validate", str(sra_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
except FileNotFoundError:
    raise RuntimeError(
        "vdb-validate not found. Please install SRA Toolkit."
    )

if result.returncode != 0:
    raise RuntimeError(
        f"vdb-validate failed:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

ok_file.parent.mkdir(parents=True, exist_ok=True)

log_file = ok_file.with_suffix(".log")

log_file.write_text(
    f"Command: vdb-validate {sra_file}\n\n"
    f"STDOUT:\n{result.stdout}\n\n"
    f"STDERR:\n{result.stderr}\n"
)

ok_file.write_text(
    f"{datetime.now().isoformat()}\t{sra_file.name}\tPASS\n"
)