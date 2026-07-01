# Pre-label Tool

Multi-view pre-labeling tool for Orin recordings.

The tool reads recorded sequences directly from Orin local storage, lets a user pre-label metadata and bounding boxes in a browser UI, then uploads the completed sequence to PDX/CSS.

## Source recordings path

The source recordings are on Orin at:

```text
/mnt/nova_ssd/recordings
```

Each sequence should be a folder under that path:

```text
/mnt/nova_ssd/recordings/<sequence_name>/
```

## Workflow

```text
Orin recordings
/mnt/nova_ssd/recordings/<sequence_name>/
        ↓
Pre-label UI reads videos locally from Orin
        ↓
User fills metadata and draws bounding boxes
        ↓
Submit uploads 4 videos + hoi_metadata.yaml to PDX/CSS
        ↓
Next sequence appears
```

## Required sequence format

Each sequence folder must contain these 4 videos:

```text
front_stereo_camera_left.mp4
back_stereo_camera_left.mp4
left_stereo_camera_left.mp4
right_stereo_camera_left.mp4
```

After labeling, the tool uploads these files to PDX/CSS:

```text
front_stereo_camera_left.mp4
back_stereo_camera_left.mp4
left_stereo_camera_left.mp4
right_stereo_camera_left.mp4
hoi_metadata.yaml
```

## Run on Orin

### Terminal 1: SSH into Orin and start the app

```bash
ssh nvidia@nova-devkit-6.dyn.nvidia.com
cd /path/to/prelabel-tool
source venv/bin/activate
```

Set CSS/PDX credentials in the terminal. Do not commit credentials.

```bash
export CSS_ACCESS_KEY=YOUR_ACCESS_KEY
export CSS_SECRET_KEY=YOUR_SECRET_KEY
export AWS_ACCESS_KEY_ID="$CSS_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$CSS_SECRET_KEY"
export AWS_DEFAULT_REGION="us-east-1"
```

Start the app:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 python app_orin.py
```

### Terminal 2: create SSH tunnel from Mac

On your Mac, open a second terminal:

```bash
ssh -L 8000:127.0.0.1:8000 nvidia@nova-devkit-6.dyn.nvidia.com
```

Keep this terminal open.

### Browser

Open on your Mac:

```text
http://127.0.0.1:8000
```

## How to pre-label

1. Open the displayed sequence.
2. Fill metadata:
   - `calib_sequence`
   - `object_id`
   - `person_id`
   - `action_description`
   - `action_language`
3. Draw one bounding box for each camera view:
   - `front_stereo_camera_left`
   - `back_stereo_camera_left`
   - `left_stereo_camera_left`
   - `right_stereo_camera_left`
4. Click `Submit`.

After submit, the tool uploads the completed sequence to PDX/CSS and moves to the next ready sequence.

## Run one specific sequence

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 SEQUENCE_NAME=<sequence_name> python app_orin.py
```

Example:

```bash
CONFIG_PATH=config_prod.yaml ALLOW_PROD_UPLOAD=1 LOCAL_RECORDINGS_DIR=/mnt/nova_ssd/recordings ONE_AT_A_TIME=1 SEQUENCE_NAME=my_sequence_001 python app_orin.py
```

## Local test

For local testing without Orin, use local `videos/` as fake Orin recordings:

```bash
CONFIG_PATH=config_test.yaml LOCAL_RECORDINGS_DIR=videos ONE_AT_A_TIME=1 python app_orin.py
```

Open:

```text
http://127.0.0.1:8000
```

## Troubleshooting

### No sequences show up

Check:

- `LOCAL_RECORDINGS_DIR` is correct
- source path exists: `/mnt/nova_ssd/recordings`
- sequence folder contains all 4 required videos
- `SEQUENCE_NAME` matches the folder name, if used
- credentials are set
- config path is correct

### Port already in use

Stop old Flask process with `Ctrl+C`, or run:

```bash
lsof -i :8000
```

## Fresh setup / clone instructions

Use this if setting up the tool on a new machine.

Clone the repo:

```bash
git clone https://github.com/rishitat-tech/prelabel-tool.git
cd prelabel-tool
```

Create and activate Python environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then follow the Run on Orin section above.
