# Pre-label Tool

Multi-view pre-labeling tool for Orin recordings.

Main workflow: run the tool on Orin, read recordings from /mnt/nova_ssd/recordings, label in browser, upload completed sequence to PDX/CSS.

## What the tool does

1. Reads local Orin sequence folders from /mnt/nova_ssd/recordings
2. Shows one ready sequence in the browser
3. User fills metadata and draws bounding boxes
4. Submit uploads 4 videos plus hoi_metadata.yaml to PDX/CSS
5. Tool writes local completion markers
6. Completed sequence disappears and next ready sequence appears

## Required Orin source path

Recordings are expected here:

```text
/mnt/nova_ssd/recordings
```

Each sequence should be a folder like:

```text
/mnt/nova_ssd/recordings/<sequence_name>/
```

## Required sequence files

Each sequence folder must contain these 4 MP4 files:

```text
front_stereo_camera_left.mp4
back_stereo_camera_left.mp4
left_stereo_camera_left.mp4
right_stereo_camera_left.mp4
```

If the sequence only has PNGs under frame_0, generate MP4 previews first:

```bash
SEQ=/mnt/nova_ssd/recordings/<sequence_name>; for view in front_stereo_camera_left back_stereo_camera_left left_stereo_camera_left right_stereo_camera_left; do ffmpeg -y -loop 1 -framerate 30 -i "$SEQ/frame_0/${view}.png" -t 1 -c:v libx264 -pix_fmt yuv420p "$SEQ/${view}.mp4"; done
```

## One-time setup on Orin

SSH into Orin:

```bash
ssh nvidia@nova-devkit-6.dyn.nvidia.com
```

Clone repo if needed:

```bash
cd /home/nvidia && git clone https://github.com/rishitat-tech/prelabel-tool.git
```

Set up environment:

```bash
cd /home/nvidia/prelabel-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Set credentials on Orin

Do not commit or share credentials.

```bash
export CSS_ACCESS_KEY=YOUR_ACCESS_KEY
export CSS_SECRET_KEY=YOUR_SECRET_KEY
export AWS_ACCESS_KEY_ID="$CSS_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$CSS_SECRET_KEY"
export AWS_DEFAULT_REGION="us-east-1"
```

## Main Orin usage

### Terminal 1: start app on Orin

Run this from inside the Orin SSH session:

```bash
cd /home/nvidia/prelabel-tool && source venv/bin/activate && CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 AUTO_OPEN_BROWSER=0 python app_orin.py
```

Leave this terminal open. Expected output includes:

```text
Running on http://127.0.0.1:8000
```

### Terminal 2: open SSH tunnel from Mac

Open a second Mac terminal and run:

```bash
ssh -N -L 8001:127.0.0.1:8000 nvidia@nova-devkit-6.dyn.nvidia.com
```

This terminal may look stuck. That is normal. Leave it open.

### Browser

Open on Mac:

```text
http://127.0.0.1:8001
```

## How to pre-label

1. Open the displayed sequence.
2. Fill metadata: calib_sequence, object_id, person_id, action_description, action_language.
3. Draw one bounding box for each camera view: front, back, left, right.
4. Click Submit.

## After submit

The tool uploads these files to PDX/CSS:

```text
front_stereo_camera_left.mp4
back_stereo_camera_left.mp4
left_stereo_camera_left.mp4
right_stereo_camera_left.mp4
hoi_metadata.yaml
```

It also writes local completion files on Orin:

```text
/mnt/nova_ssd/recordings/<sequence_name>/hoi_metadata.yaml
/mnt/nova_ssd/recordings/<sequence_name>/.prelabel_uploaded
```

These local files hide completed sequences from the ready list.

## Relabel a sequence

If the label was wrong, delete only local completion files:

```bash
rm /mnt/nova_ssd/recordings/<sequence_name>/hoi_metadata.yaml
rm /mnt/nova_ssd/recordings/<sequence_name>/.prelabel_uploaded
```

Then rerun the app. The sequence appears again. Submitting again uploads to the same PDX/CSS path.

## Free Orin disk space

After confirming upload is complete, delete the local Orin sequence folder to free space:

```bash
rm -rf /mnt/nova_ssd/recordings/<sequence_name>/
```

This deletes local Orin files only. It does not delete PDX/CSS uploads.

## Bulk cleanup in small batches

Preview 5 completed local sequence folders:

```bash
cd /home/nvidia/prelabel-tool && source venv/bin/activate && CLEANUP_LIMIT=5 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings python cleanup_completed_orin_sequences.py
```

Actually delete 5 completed local sequence folders:

```bash
cd /home/nvidia/prelabel-tool && source venv/bin/activate && DRY_RUN=0 ALLOW_DELETE_LOCAL=1 CLEANUP_LIMIT=5 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings python cleanup_completed_orin_sequences.py
```

## Run one specific sequence

```bash
cd /home/nvidia/prelabel-tool && source venv/bin/activate && CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 AUTO_OPEN_BROWSER=0 SEQUENCE_NAME=<sequence_name> python app_orin.py
```

## Troubleshooting

If python cannot open app_orin.py, run from the repo folder:

```bash
cd /home/nvidia/prelabel-tool
```

Check app on Orin:

```bash
curl -I http://127.0.0.1:8000
```

Check tunnel on Mac:

```bash
curl -I http://127.0.0.1:8001
```

If no sequences show, check MP4 files and local completion markers:

```bash
ls -lh /mnt/nova_ssd/recordings/<sequence_name>/*.mp4
ls -lah /mnt/nova_ssd/recordings/<sequence_name> | grep -E "hoi_metadata|prelabel"
```
