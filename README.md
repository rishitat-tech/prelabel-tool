# Pre-label Tool

Multi-view pre-labeling tool for Orin recordings.

The tool reads recorded sequences from Orin local storage, lets a user pre-label metadata and bounding boxes in a browser UI, then uploads the completed sequence to PDX/CSS.

## Workflow

```text
Orin recordings:
  /mnt/nova_ssd/recordings/<sequence_name>/

Tool reads videos locally from Orin
→ user fills metadata and draws bounding boxes
→ Submit uploads videos + hoi_metadata.yaml to PDX/CSS
→ next sequence appears
```

## Required sequence format

Each sequence folder must contain these 4 videos:

```text
front_stereo_camera_left.mp4
back_stereo_camera_left.mp4
left_stereo_camera_left.mp4
right_stereo_camera_left.mp4
```

After labeling, the tool uploads the 4 videos plus:

```text
hoi_metadata.yaml
```

## Clone the repo

```bash
git clone https://github.com/rishitat-tech/prelabel-tool.git
cd prelabel-tool
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Credentials

Set CSS/PDX credentials in the terminal. Do not commit credentials.

```bash
export CSS_ACCESS_KEY=YOUR_ACCESS_KEY
export CSS_SECRET_KEY=YOUR_SECRET_KEY
export AWS_ACCESS_KEY_ID="$CSS_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$CSS_SECRET_KEY"
export AWS_DEFAULT_REGION="us-east-1"
```

## Local test

Use local videos folder as fake Orin recordings:

```bash
CONFIG_PATH=config_test.yaml LOCAL_RECORDINGS_DIR=videos ONE_AT_A_TIME=1 python app_orin.py
```

Open:

```text
http://127.0.0.1:8000
```

## Real Orin usage

### Terminal 1: SSH into Orin and run app

```bash
ssh nvidia@nova-devkit-6.dyn.nvidia.com
cd /path/to/prelabel-tool
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

Run app:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 python app_orin.py
```

### Terminal 2: SSH tunnel from Mac

On Mac:

```bash
ssh -L 8000:127.0.0.1:8000 nvidia@nova-devkit-6.dyn.nvidia.com
```

Keep this terminal open.

### Browser

Open on Mac:

```text
http://127.0.0.1:8000
```

## How to pre-label

1. Open the displayed sequence.
2. Fill metadata: calib_sequence, object_id, person_id, action_description, action_language.
3. Draw one bounding box for each camera view: front, back, left, right.
4. Click Submit.

After submit, the tool uploads the completed sequence to PDX/CSS and moves to the next ready sequence.

## Run one specific sequence

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 SEQUENCE_NAME=<sequence_name> python app_orin.py
```

## Troubleshooting

If no sequences show up, check:

- LOCAL_RECORDINGS_DIR is correct
- sequence folder contains all 4 required videos
- SEQUENCE_NAME matches the folder name, if used
- credentials are set
- config path is correct

If port is already in use, stop old Flask process with Ctrl+C or run:

```bash
lsof -i :8000
```
