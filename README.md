# Pre-label Tool

Multi-view pre-labeling tool for local Orin recordings. The tool reads recorded sequences from a local folder on Orin, lets a user label metadata and bounding boxes in a browser UI, then uploads the completed sequence to PDX/CSS.

## Workflow

```text
Orin recordings:
  /mnt/nova_ssd/recordings/<sequence_name>/

Tool reads videos locally from Orin
→ user fills metadata and draws bounding boxes
→ Submit uploads videos + hoi_metadata.yaml to PDX/CSS
→ next sequence appears

