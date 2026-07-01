import os
import shutil
from pathlib import Path


def main():
    recordings_dir = Path(os.getenv("LOCAL_RECORDINGS_DIR", "/mnt/nova_ssd/recordings"))
    dry_run = os.getenv("DRY_RUN", "1") != "0"
    allow_delete = os.getenv("ALLOW_DELETE_LOCAL", "0") == "1"

    if not recordings_dir.exists():
        raise SystemExit(f"Recordings dir does not exist: {recordings_dir}")

    completed = []

    for seq_dir in sorted(recordings_dir.iterdir()):
        if not seq_dir.is_dir():
            continue

        marker = seq_dir / ".prelabel_uploaded"

        if marker.exists():
            completed.append(seq_dir)

    print(f"Recordings dir: {recordings_dir}")
    print(f"Completed sequence folders found: {len(completed)}")
    print()

    for seq_dir in completed:
        if dry_run:
            print(f"Would delete: {seq_dir}")
        else:
            print(f"Deleting: {seq_dir}")

    print()

    if dry_run:
        print("Dry run only. Nothing deleted.")
        print("To actually delete completed local sequences, run:")
        print("  DRY_RUN=0 ALLOW_DELETE_LOCAL=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings python cleanup_completed_orin_sequences.py")
        return

    if not allow_delete:
        raise SystemExit("Refusing to delete. Set ALLOW_DELETE_LOCAL=1.")

    for seq_dir in completed:
        shutil.rmtree(seq_dir)

    print(f"Deleted {len(completed)} completed sequence folders.")


if __name__ == "__main__":
    main()
