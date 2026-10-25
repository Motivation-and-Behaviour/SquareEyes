#!/usr/bin/env python3
"""
Replaces blank DateTime values in existing "Image Data Import.csv" files with a
sentinel date, since newer versions of Timelapse refuse to import blanks (#28).

Edits the files in place on OneDrive.
"""

import argparse
import csv
import logging
import time
from pathlib import Path

# Also sets up logging to workflow_errors.log
from find_and_copy_unprocessed import get_config
from tqdm import tqdm

# --- CONFIGURATION ---
MISSING_DATETIME = "9999-12-31 23:59:59"  # Keep in sync with src/processing/process.py
CSV_NAME = "Image Data Import.csv"
MAX_RETRY_PASSES = 5
RETRY_WAIT = 60  # Seconds between retry passes, gives OneDrive time to download


def find_csvs(src_base):
    """Finds the import CSV in every participant/timepoint folder."""
    return sorted(
        p
        for p in src_base.glob(f"*/*/Images/{CSV_NAME}")
        if p.parts[len(src_base.parts)] != "Practice Data"
    )


def fix_file(path, dry_run=False):
    """Replaces blank DateTimes in a single CSV. Returns the number of rows changed."""
    with open(path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames or "DateTime" not in fieldnames:
        logging.error(f"No DateTime column: {path}")
        return 0

    n_changed = 0
    for row in rows:
        if not (row["DateTime"] or "").strip():
            row["DateTime"] = MISSING_DATETIME
            n_changed += 1

    if n_changed and not dry_run:
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return n_changed


def run_pass(paths, dry_run, desc):
    """Attempts every file once. Returns ({path: rows changed}, [failed paths])."""
    results, failed = {}, []
    for path in tqdm(paths, unit="file", desc=desc):
        try:
            results[path] = fix_file(path, dry_run)
        except OSError as e:
            logging.error(f"Fix failed {path}: {e}")
            failed.append(path)
    return results, failed


def main():
    parser = argparse.ArgumentParser(
        description=f"Replace blank DateTimes in '{CSV_NAME}' with {MISSING_DATETIME}"
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Folder containing participant folders (defaults to config.ini)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing anything",
    )
    args = parser.parse_args()

    src_base = args.root if args.root else get_config()[0]

    print(f"--- Square Eyes DateTime Fix{' (DRY RUN)' if args.dry_run else ''} ---")
    print(f"Source: {src_base}\n")

    paths = find_csvs(src_base)
    print(f"Found {len(paths)} '{CSV_NAME}' files")

    results, failed = run_pass(paths, args.dry_run, "Fixing")

    for retry_pass in range(1, MAX_RETRY_PASSES + 1):
        if not failed:
            break
        print(
            f"\n{len(failed)} files failed. Waiting {RETRY_WAIT}s before retry "
            f"pass {retry_pass}/{MAX_RETRY_PASSES}..."
        )
        time.sleep(RETRY_WAIT)
        retried, still_failed = run_pass(failed, args.dry_run, f"Retry {retry_pass}")
        results.update(retried)
        if len(still_failed) == len(failed):
            print("No progress on this pass, giving up on retries.")
            failed = still_failed
            break
        failed = still_failed

    fixed = {p: n for p, n in results.items() if n}
    verb = "Would fix" if args.dry_run else "Fixed"
    for path, n in fixed.items():
        print(f"  {verb} {n:>6} rows in {path.relative_to(src_base)}")

    print(
        f"\nDone. {verb} {sum(fixed.values())} rows in {len(fixed)} files, "
        f"{len(results) - len(fixed)} unchanged, {len(failed)} failed."
    )
    if failed:
        print("Failed files (see workflow_errors.log):")
        for path in failed:
            print(f"  {path}")


if __name__ == "__main__":
    main()
