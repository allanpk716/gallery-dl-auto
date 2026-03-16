"""Batch download R18 rankings"""
import subprocess
import sys
import time
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

tasks = [
    ("day_r18", 179),
    ("day_male_r18", 432),
    ("week_r18", 172),
]

for mode, total in tasks:
    print(f"\n{'='*60}")
    print(f"Start: {mode} (expected ~{total} works)")
    print(f"{'='*60}")
    
    cmd = [
        "pixiv-downloader", "download",
        "--type", mode,
        "--format", "jsonl",
        "--image-delay", "1.5",
    ]
    
    start = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=1800,
        cwd=r"C:\WorkSpace\gallery-dl-auto",
    )
    elapsed = time.time() - start
    
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines[-3:]:
            print(line)
    
    if result.returncode == 0:
        print(f"[OK] {mode} done ({elapsed:.0f}s)")
    else:
        print(f"[FAIL] {mode} rc={result.returncode} ({elapsed:.0f}s)")
        if result.stderr:
            print(f"stderr: {result.stderr[:500]}")
    
    time.sleep(5)

print("\nAll done!")
