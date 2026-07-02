# Pre-label Tool

Multi-view pre-labeling tool for Orin recordings.

Main workflow: run the tool on the shared Orin, read recordings from /mnt/nova_ssd/recordings, label in a browser, and upload the completed sequence to PDX/CSS.

## Important: setup is only needed once

This project uses one shared Orin:

```bash
nvidia@nova-devkit-6.dyn.nvidia.com
```

The one-time setup only needs to be done once on that Orin by one person/admin.
After setup is done, everyone else should skip setup and follow Daily Usage.

## Workflow

```text
Orin recordings
/mnt/nova_ssd/recordings/<sequence_name>/
        ↓
Pre-label UI reads local videos from Orin
        ↓
User fills metadata and draws bounding boxes
        ↓
Submit uploads 4 videos + hoi_metadata.yaml to PDX/CSS
        ↓
Local completion markers are written
        ↓
Completed sequence disappears and next ready sequence appears
```

## Required sequence format

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

# Daily Usage: recordings on Orin

Use this for normal pre-labeling.

## Terminal 1: start app on Orin

From your Mac terminal:

```bash
ssh nvidia@nova-devkit-6.dyn.nvidia.com
```

On Orin, go to the repo:

```bash
cd /home/nvidia/prelabel-tool
```

Activate environment:

```bash
source venv/bin/activate
```

Set credentials:

```bash
export CSS_ACCESS_KEY=YOUR_ACCESS_KEY
export CSS_SECRET_KEY=YOUR_SECRET_KEY
export AWS_ACCESS_KEY_ID="$CSS_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$CSS_SECRET_KEY"
export AWS_DEFAULT_REGION="us-east-1"
```

Generate the 4 MP4 videos from the MCAP before labeling:

```bash
python extract_mcap_videos.py /mnt/nova_ssd/recordings/<sequence_name>
```

For quick testing, extract only the first 300 frames:

```bash
MAX_FRAMES=300 python extract_mcap_videos.py /mnt/nova_ssd/recordings/<sequence_name>
```

This creates:

```text
front_stereo_camera_left.mp4
back_stereo_camera_left.mp4
left_stereo_camera_left.mp4
right_stereo_camera_left.mp4
```

Start app:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 AUTO_OPEN_BROWSER=0 python app_orin.py
```

Leave this terminal open. Expected output:

```text
Running on http://127.0.0.1:8000
```

## Terminal 2: open SSH tunnel from Mac

Open a second Mac terminal and run:

```bash
ssh -N -L 8001:127.0.0.1:8000 nvidia@nova-devkit-6.dyn.nvidia.com
```

This terminal may look stuck. That is normal. Leave it open.

## Browser

Open on your Mac:

```text
http://127.0.0.1:8001
```

You should see one ready sequence.

## How to pre-label

1. Open the displayed sequence.
2. Fill metadata:
   - calib_sequence
   - object_id
   - person_id
   - action_description
   - action_language
3. Draw one bounding box for each camera view:
   - front_stereo_camera_left
   - back_stereo_camera_left
   - left_stereo_camera_left
   - right_stereo_camera_left
4. Click Submit.

After submit, the sequence uploads to PDX/CSS and the next ready sequence appears.

## What happens after submit

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

Deleting local completion files does not delete anything from PDX/CSS.

## Free Orin disk space

After confirming upload is complete, delete the local Orin sequence folder to free space:

```bash
rm -rf /mnt/nova_ssd/recordings/<sequence_name>/
```

This deletes local Orin files only. It does not delete uploaded files from PDX/CSS.

## Bulk cleanup in small batches

Preview 5 completed local sequence folders:

```bash
cd /home/nvidia/prelabel-tool && source venv/bin/activate && CLEANUP_LIMIT=5 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings python cleanup_completed_orin_sequences.py
```

Actually delete 5 completed local sequence folders:

```bash
cd /home/nvidia/prelabel-tool && source venv/bin/activate && DRY_RUN=0 ALLOW_DELETE_LOCAL=1 CLEANUP_LIMIT=5 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings python cleanup_completed_orin_sequences.py
```

This only deletes local Orin folders. It does not delete from PDX/CSS.

# Optional: run with local downloaded recordings

Use this only if recordings are already downloaded to your Mac/local machine.

Example local source path:

```text
/Users/<your_user>/recordings
```

Start app locally:

```bash
cd /path/to/prelabel-tool && source venv/bin/activate && CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/Users/<your_user>/recordings ONE_AT_A_TIME=1 python app_orin.py
```

Open browser directly:

```text
http://127.0.0.1:8000
```

No SSH tunnel is needed for local mode.

# One-time setup on Orin

Only needed once on the shared Orin.

```bash
ssh nvidia@nova-devkit-6.dyn.nvidia.com
cd /home/nvidia
git clone https://github.com/rishitat-tech/prelabel-tool.git
cd /home/nvidia/prelabel-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

After this, users should follow Daily Usage.

# Troubleshooting

## python cannot open app_orin.py

You are in the wrong folder. Run:

```bash
cd /home/nvidia/prelabel-tool
```

## Browser does not open

Make sure Terminal 1 is running the app and Terminal 2 is running the tunnel.

Check app on Orin:

```bash
curl -I http://127.0.0.1:8000
```

Check tunnel on Mac:

```bash
curl -I http://127.0.0.1:8001
```

## No sequences show up

Check that the sequence has the 4 required MP4s:

```bash
ls -lh /mnt/nova_ssd/recordings/<sequence_name>/*.mp4
```

Check if it is already marked complete:

```bash
ls -lah /mnt/nova_ssd/recordings/<sequence_name> | grep -E "hoi_metadata|prelabel"
```
