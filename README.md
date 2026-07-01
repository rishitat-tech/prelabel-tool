# Pre-label Tool

Multi-view pre-labeling tool for Orin recordings.

The tool reads recorded sequences from either Orin local storage or a local downloaded recordings folder, lets a user pre-label metadata and bounding boxes in a browser UI, then uploads the completed sequence to PDX/CSS.

## Source recordings path on Orin

Recordings on Orin are stored at:

```text
/mnt/nova_ssd/recordings
```

Each sequence should be under:

```text
/mnt/nova_ssd/recordings/<sequence_name>/
```

## Workflow

```text
Recording sequence folder
→ Pre-label UI reads videos locally
→ User fills metadata and draws bounding boxes
→ Submit uploads 4 videos + hoi_metadata.yaml to PDX/CSS
→ Next sequence appears
```

## Required sequence format

Each sequence folder must contain:

```text
front_stereo_camera_left.mp4
back_stereo_camera_left.mp4
left_stereo_camera_left.mp4
right_stereo_camera_left.mp4
```

After labeling, the tool uploads those 4 videos plus:

```text
hoi_metadata.yaml
```

## Option A: Run using recordings directly on Orin

Use this when recordings are on Orin at `/mnt/nova_ssd/recordings`.

### Terminal 1: SSH into Orin and start app

```bash
ssh nvidia@nova-devkit-6.dyn.nvidia.com
cd /path/to/prelabel-tool
source venv/bin/activate
```

Set CSS/PDX credentials:

```bash
export CSS_ACCESS_KEY=YOUR_ACCESS_KEY
export CSS_SECRET_KEY=YOUR_SECRET_KEY
export AWS_ACCESS_KEY_ID=\"$CSS_ACCESS_KEY\"
export AWS_SECRET_ACCESS_KEY=\"$CSS_SECRET_KEY\"
export AWS_DEFAULT_REGION=\"us-east-1\"
```

Start app on Orin:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 python app_orin.py
```

### Terminal 2: SSH tunnel from Mac

Open a second terminal on Mac:

```bash
ssh -L 8000:127.0.0.1:8000 nvidia@nova-devkit-6.dyn.nvidia.com
```

Keep this terminal open.

### Browser on Mac

Open:

```text
http://127.0.0.1:8000
```

The UI should show one ready sequence. After submit, it uploads the completed sequence and moves to the next one.

## Option B: Run using recordings downloaded locally

Use this when recordings are already downloaded to your Mac or local machine.

Example local recordings path:

```text
/Users/rishitathota/recordings
```

Expected structure:

```text
/Users/rishitathota/recordings/<sequence_name>/
  front_stereo_camera_left.mp4
  back_stereo_camera_left.mp4
  left_stereo_camera_left.mp4
  right_stereo_camera_left.mp4
```

Run locally:

```bash
cd /Users/rishitathota/pre-label
source venv/bin/activate
```

Set credentials:

```bash
export CSS_ACCESS_KEY=YOUR_ACCESS_KEY
export CSS_SECRET_KEY=YOUR_SECRET_KEY
export AWS_ACCESS_KEY_ID=\"$CSS_ACCESS_KEY\"
export AWS_SECRET_ACCESS_KEY=\"$CSS_SECRET_KEY\"
export AWS_DEFAULT_REGION=\"us-east-1\"
```

Start app using local downloaded recordings:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/Users/rishitathota/recordings ONE_AT_A_TIME=1 python app_orin.py
```

Open directly:

```text
http://127.0.0.1:8000
```

No SSH tunnel is needed when running locally.

## Local safe test

For testing without production upload:

```bash
CONFIG_PATH=config_test.yaml LOCAL_RECORDINGS_DIR=videos ONE_AT_A_TIME=1 python app_orin.py
```

Open:

```text
http://127.0.0.1:8000
```

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

After submit, the tool uploads the completed sequence to PDX/CSS and moves to the next ready sequence.

## Run one specific sequence

For Orin recordings:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 SEQUENCE_NAME=<sequence_name> python app_orin.py
```

For local downloaded recordings:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/Users/rishitathota/recordings ONE_AT_A_TIME=1 SEQUENCE_NAME=<sequence_name> python app_orin.py
```

## Troubleshooting

If no sequences show up, check:

- LOCAL_RECORDINGS_DIR is correct
- source path exists
- sequence folder contains all 4 required videos
- SEQUENCE_NAME matches the folder name if used
- credentials are set
- config path is correct

If port is already in use, stop old Flask process with Ctrl+C, or run:

```bash
lsof -i :8000
```

## Fresh setup / clone instructions

Use this if setting up the tool on a new machine.

```bash
git clone https://github.com/rishitat-tech/prelabel-tool.git
cd prelabel-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then follow Option A or Option B above.
