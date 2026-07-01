import sys
from pathlib import Path

from css_client import CssClient, load_config, REQUIRED_VIDEOS


def main():
    sequence_name = sys.argv[1] if len(sys.argv) > 1 else "sample_sequence"

    local_dir = Path("videos") / sequence_name

    if not local_dir.exists():
        raise SystemExit(f"Missing local folder: {local_dir}")

    config = load_config()
    client = CssClient(config)

    if "multiview_test" not in client.base_prefix:
        raise SystemExit(f"Refusing to upload outside test prefix: {client.base_prefix}")

    print("Uploading to TEST prefix only:")
    print(f"  bucket: {client.bucket}")
    print(f"  prefix: {client.sequence_prefix(sequence_name)}")
    print()

    for video_name in REQUIRED_VIDEOS:
        local_path = local_dir / video_name

        if not local_path.exists():
            raise SystemExit(f"Missing local video: {local_path}")

        key = client.upload_file(local_path, sequence_name, video_name)
        print(f"Uploaded {local_path} -> s3://{client.bucket}/{key}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
