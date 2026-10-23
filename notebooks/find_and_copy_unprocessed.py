#!/usr/bin/env python3
import configparser
import csv
import logging
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tqdm import tqdm

# --- CONFIGURATION ---
logging.basicConfig(
    filename="workflow_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

MAX_WORKERS = 8
RETRY_WORKERS = 2  # Fewer workers on retry passes to go easy on OneDrive
MAX_RETRY_PASSES = 5
RETRY_WAIT = 60  # Seconds between retry passes, gives OneDrive time to download
CSV_FILE = "unprocessed_folders.csv"


def get_config():
    """Robust configuration loader."""
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir.parent / "config.ini"

    config = configparser.ConfigParser()
    if not config_path.exists():
        print(f"[ERROR] Config file not found at: {config_path}")
        sys.exit(1)
    config.read(config_path)

    src = Path(config["DEFAULT"]["folder_prefix"])
    dst = Path(r"~/Projects/square_eyes_tmp").expanduser()

    if not src.exists():
        print(f"[ERROR] Source base directory does not exist: {src}")
        sys.exit(1)

    return src, dst


def ensure_dir(path):
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def copy_worker(src, dst, pbar):
    """
    Copies the file and updates the progress bar automatically.
    Skips files already copied. Makes a single attempt and returns the error
    (or None on success) so failures can be retried later without blocking.
    """
    try:
        # Skip files already copied in full (makes re-runs cheap)
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            return None
        if not dst.parent.exists():
            ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return None
    except Exception as e:
        # copy2 creates dst before reading src, so a failed read
        # leaves an empty/partial file behind - remove it
        try:
            dst.unlink(missing_ok=True)
        except OSError:
            pass
        return e
    finally:
        # Update progress bar (thread-safe in modern tqdm)
        pbar.update(1)


def retry_failed(failed):
    """
    Retries failed copies in passes, waiting between passes so OneDrive has
    time to download the files. Returns the copies that still failed.
    """
    for retry_pass in range(1, MAX_RETRY_PASSES + 1):
        if not failed:
            break
        print(
            f"\n{len(failed)} files failed. Waiting {RETRY_WAIT}s before retry "
            f"pass {retry_pass}/{MAX_RETRY_PASSES}..."
        )
        time.sleep(RETRY_WAIT)

        pbar = tqdm(total=len(failed), unit="file", desc=f"Retry {retry_pass}")
        with ThreadPoolExecutor(max_workers=RETRY_WORKERS) as executor:
            futures = [
                (src, dst, executor.submit(copy_worker, src, dst, pbar))
                for src, dst, _ in failed
            ]
        pbar.close()

        still_failed = [
            (src, dst, f.result()) for src, dst, f in futures if f.result()
        ]
        if len(still_failed) == len(failed):
            print("No progress on this pass, giving up on retries.")
            failed = still_failed
            break
        failed = still_failed

    return failed


def load_folders_from_csv():
    """Reads the existing CSV to skip scanning."""
    if not os.path.exists(CSV_FILE):
        return []

    print(f"Found existing job file: {CSV_FILE}")
    choice = input("Resuming from file? (y/n): ").strip().lower()
    if choice != "y":
        return []

    folders = []
    try:
        with open(CSV_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert path string back to Path object
                row["src"] = Path(row["src"])
                folders.append(row)
        print(f"Loaded {len(folders)} folders from file.")
        return folders
    except Exception as e:
        print(f"Error loading CSV: {e}. Starting fresh.")
        return []


def scan_for_folders(src_base):
    """Scans the network drive for unprocessed data."""
    print("Scanning OneDrive for participants...")
    participants = [
        p for p in src_base.iterdir() if p.is_dir() and p.name != "Practice Data"
    ]

    folders = []
    for p in tqdm(participants, desc="Locating Data Folders"):
        for timepoint in p.iterdir():
            images_root = timepoint / "Images"
            images_sub = images_root / "images"
            converted = images_root / ".converted"

            if images_root.exists() and images_sub.exists() and not converted.exists():
                folders.append(
                    {"src": images_root, "id": p.name, "timepoint": timepoint.name}
                )
    return folders


def save_folders_to_csv(folders):
    """Saves the list so we can resume later."""
    try:
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["src", "id", "timepoint"])
            writer.writeheader()
            writer.writerows(folders)
        print(f"Saved job list to {CSV_FILE}")
    except Exception as e:
        print(f"Warning: Could not save CSV: {e}")


def main():
    SRC_BASE, DST_DIR = get_config()

    print(f"--- Square Eyes Streaming Workflow ---")
    print(f"Source: {SRC_BASE}")
    print(f"Dest:   {DST_DIR}\n")

    # --- PHASE 1: IDENTIFY PARTICIPANTS (RESUME LOGIC) ---
    folders_to_process = load_folders_from_csv()

    if not folders_to_process:
        folders_to_process = scan_for_folders(SRC_BASE)
        if folders_to_process:
            save_folders_to_csv(folders_to_process)

    if not folders_to_process:
        print("No folders found to process. Exiting.")
        sys.exit(0)

    # --- PHASE 2: STREAMING COPY ---
    print(f"\nStarting streaming copy for {len(folders_to_process)} folders...")

    local_processed_paths = []

    # FIX: Initialize total=0 so we can increment it later without TypeError
    pbar = tqdm(total=0, unit="file", smoothing=0.1, desc="Copying")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []

        # PRODUCER: Main thread walks folders
        for folder_info in folders_to_process:
            src_dir = folder_info["src"]

            try:
                rel_path = src_dir.relative_to(SRC_BASE)
                local_dir = DST_DIR / rel_path
                local_processed_paths.append(local_dir)
            except ValueError:
                continue

            # Walk source
            for root, dirs, files in os.walk(src_dir):
                for file in files:
                    src_file = Path(root) / file
                    rel_file = src_file.relative_to(src_dir)
                    dst_file = local_dir / rel_file

                    # Increment Total (Dynamic Bar)
                    pbar.total += 1

                    # Submit task
                    futures.append(
                        (
                            src_file,
                            dst_file,
                            executor.submit(copy_worker, src_file, dst_file, pbar),
                        )
                    )

                # Refresh bar periodically in main loop so total updates visually
                pbar.refresh()

    pbar.close()

    # Collect failures from the first pass and retry them later in batches
    failed = [(src, dst, f.result()) for src, dst, f in futures if f.result()]
    failed = retry_failed(failed)

    for src, dst, e in failed:
        logging.error(f"Copy error: {src} -> {e}")
    if failed:
        print(f"\n{len(failed)} files could not be copied (see workflow_errors.log)")

    # --- PHASE 3: EXTERNAL PROCESSING ---
    local_paths_str = " ".join([f'"{str(p)}"' for p in local_processed_paths])
    processing_command = f"python SquareEyes.py -f {local_paths_str}"

    # Check for empty images left by failed copies (these crash SquareEyes.py)
    empty_counts = {}
    for local_dir in local_processed_paths:
        n_empty = sum(
            1
            for f in local_dir.rglob("*")
            if f.suffix.lower() == ".jpg" and f.stat().st_size == 0
        )
        if n_empty:
            empty_counts[local_dir] = n_empty

    print("\n" + "=" * 60)
    if empty_counts:
        print("WARNING: EMPTY IMAGES FOUND")
        print("=" * 60)
        for local_dir, n_empty in empty_counts.items():
            print(f"  {n_empty:>6} empty images in {local_dir}")
        print("\nRe-run this script to re-copy them before processing.")
    else:
        print("READY FOR PROCESSING (no empty images found)")
    print("=" * 60)
    print(f"\n{processing_command}\n")
    print("=" * 60)
    print(">>> PAUSED. Run the command above.")
    print(">>> Press ENTER when finished to sync results back.")
    try:
        input()
    except KeyboardInterrupt:
        sys.exit(0)

    # --- PHASE 4: SYNC BACK ---
    print("\nSyncing Results to Network...")

    files_to_sync = [
        ".converted",
        "Image Data Import.csv",
        "Square Eyes Detections.json",
        "SquareEyes Template.tdb",
    ]

    sync_count = 0
    # Simple sync pass
    for local_dir in tqdm(local_processed_paths, desc="Syncing Folders"):
        if not local_dir.exists():
            continue

        rel_dir = local_dir.relative_to(DST_DIR)
        network_dir = SRC_BASE / rel_dir

        for fname in files_to_sync:
            src = local_dir / fname
            dst = network_dir / fname

            if src.exists():
                try:
                    shutil.copy2(src, dst)
                    sync_count += 1
                except Exception as e:
                    logging.error(f"Sync failed {src}: {e}")

    print(f"\nWorkflow Complete. Synced {sync_count} result files.")

    # --- PHASE 5: CLEANUP ---
    if os.path.exists(CSV_FILE):
        try:
            os.remove(CSV_FILE)
            print(f"Cleanup: Removed {CSV_FILE}")
        except OSError:
            print(f"Warning: Could not delete {CSV_FILE}")


if __name__ == "__main__":
    main()
