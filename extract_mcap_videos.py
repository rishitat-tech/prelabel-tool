import os
import sys
import subprocess
from pathlib import Path

from mcap.reader import make_reader
from rosbags.typesys import Stores, get_typestore


TOPIC_TO_OUTPUT = {
    "/front_stereo_camera/left/image_compressed": "front_stereo_camera_left.mp4",
    "/back_stereo_camera/left/image_compressed": "back_stereo_camera_left.mp4",
    "/left_stereo_camera/left/image_compressed": "left_stereo_camera_left.mp4",
    "/right_stereo_camera/left/image_compressed": "right_stereo_camera_left.mp4",
}


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python extract_mcap_videos.py /mnt/nova_ssd/recordings/<sequence_name>")

    seq_dir = Path(sys.argv[1])
    if not seq_dir.exists():
        raise SystemExit(f"Missing sequence folder: {seq_dir}")

    mcap_files = sorted(seq_dir.glob("*.mcap"))
    if not mcap_files:
        raise SystemExit(f"No .mcap file found in {seq_dir}")

    mcap_path = mcap_files[0]

    fps = float(os.getenv("FPS", "30"))
    max_frames = int(os.getenv("MAX_FRAMES", "0") or "0")
    sample_every = int(os.getenv("SAMPLE_EVERY", "1") or "1")

    typestore = get_typestore(Stores.ROS2_HUMBLE)

    print(f"Sequence: {seq_dir}")
    print(f"MCAP: {mcap_path}")
    print(f"FPS: {fps}")
    print(f"MAX_FRAMES: {max_frames if max_frames else 'all'}")
    print(f"SAMPLE_EVERY: {sample_every}")
    print()

    raw_paths = {
        topic: seq_dir / (Path(output).stem + ".h264")
        for topic, output in TOPIC_TO_OUTPUT.items()
    }

    handles = {topic: open(path, "wb") for topic, path in raw_paths.items()}
    counts = {topic: 0 for topic in TOPIC_TO_OUTPUT}
    seen = {topic: 0 for topic in TOPIC_TO_OUTPUT}
    formats = {}
    topics = set(TOPIC_TO_OUTPUT.keys())

    try:
        with open(mcap_path, "rb") as f:
            reader = make_reader(f)

            for schema, channel, message in reader.iter_messages():
                topic = channel.topic
                if topic not in topics:
                    continue

                seen[topic] += 1

                if sample_every > 1 and (seen[topic] - 1) % sample_every != 0:
                    continue

                if max_frames and counts[topic] >= max_frames:
                    continue

                ros_msg = typestore.deserialize_cdr(message.data, schema.name)
                fmt = getattr(ros_msg, "format", "")
                formats[topic] = fmt

                if "h264" not in str(fmt).lower():
                    print(f"Warning: topic {topic} format is {fmt}, expected h264")

                handles[topic].write(bytes(ros_msg.data))
                counts[topic] += 1

    finally:
        for h in handles.values():
            h.close()

    print("Raw H264 packet counts:")
    for topic, output in TOPIC_TO_OUTPUT.items():
        print(f"  {output}: {counts[topic]} packets, format={formats.get(topic)}")

    missing = [output for topic, output in TOPIC_TO_OUTPUT.items() if counts[topic] == 0]
    if missing:
        raise SystemExit(f"Missing output packets for: {missing}")

    print()
    print("Converting H264 streams to MP4...")

    for topic, output in TOPIC_TO_OUTPUT.items():
        raw_path = raw_paths[topic]
        out_path = seq_dir / output

        cmd = [
            "ffmpeg",
            "-y",
            "-r", str(fps),
            "-i", str(raw_path),
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_path),
        ]

        print(" ".join(cmd))
        subprocess.run(cmd, check=True)

    print()
    print("Done.")
    for topic, output in TOPIC_TO_OUTPUT.items():
        out_path = seq_dir / output
        print(f"{output}: {counts[topic]} packets -> {out_path}")


if __name__ == "__main__":
    main()
