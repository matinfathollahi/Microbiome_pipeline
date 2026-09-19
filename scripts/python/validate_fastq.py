#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import subprocess
import sys

if len(sys.argv) != 4:
    sys.exit(
        "Usage: validate_fastq.py R1.fastq.gz R2.fastq.gz output.ok"
    )

# بررسی وجود ابزارهای لازم
for tool in ("gzip", "seqkit"):
    subprocess.run(
        ["which", tool],
        check=True
    )

r1 = Path(sys.argv[1])
r2 = Path(sys.argv[2])
outfile = Path(sys.argv[3])

for f in (r1, r2):
    if not f.exists():
        raise FileNotFoundError(f)

    if f.stat().st_size == 0:
        raise ValueError(f"{f.name} is empty")

# بررسی سلامت gzip و ساختار FASTQ

for f in (r1, r2):
    subprocess.run(
        ["gzip", "-t", str(f)],
        check=True
    )



    subprocess.run(
        ["seqkit", "stats", str(f)],
        check=True
    )

# بررسی برابر بودن تعداد reads در R1 و R2
def get_read_count(f):
    result = subprocess.run(
        ["seqkit", "stats", "-T", str(f)],
        capture_output=True,
        text=True,
        check=True
    )

    lines = result.stdout.strip().splitlines()

    # آخرین خط شامل اطلاعات فایل است
    fields = lines[-1].split("\t")

    # ستون چهارم تعداد sequence هاست
    return int(fields[3])


r1_count = get_read_count(r1)
r2_count = get_read_count(r2)

if r1_count != r2_count:
    raise ValueError(
        f"Read count mismatch: R1={r1_count}, R2={r2_count}"
    )

if outfile.parent != Path("."):
    outfile.parent.mkdir(
        parents=True,
        exist_ok=True
    )

outfile.write_text(
    f"{datetime.now().isoformat()}\tPASS\n"
)