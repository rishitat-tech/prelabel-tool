import os
import sys
from pathlib import Path

from css_client import CssClient, load_config, REQUIRED_VIDEOS


def main():
    if len(sys.argv) < 3:
        raise SystemExit(
            "Usage: CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 "
            "python upload_orin_sequence.py <local_sequence_dir> <sequence_name>"
        )

    local_dir = Path(sys.argv[1])
    sequence_name = sys.argv[2]

    if not local_dir.exists():
        raise SystemExit(f"Missing local folder: {local_dir}")

    config = load_config(os.getenv("CONFIG_PATH", "config.yaml"))
    client = CssClient(config)

    if "multiview_test" not in client.base_prefix and os.getenv("ALLOW_PROD_UPLOAD") != "1":
        raise SystemExit(
            f"Refusing to upload outside test prefix: {client.base_prefix}. "
            "Set ALLOW_PROD_UPLOAD=1 if intentional."
        )

    print("Uploading sequence:")
    print(f"  local: {local_dir}")
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
