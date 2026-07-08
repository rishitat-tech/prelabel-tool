from flask import Flask, render_template_string, request, jsonify, send_file, abort
import os
import json
from datetime import datetime, timezone

import re
import yaml
import webbrowser
import threading
import subprocess
from pathlib import Path

from css_client import CssClient, load_config, CAMERA_VIEWS

app = Flask(__name__)

config = load_config(os.getenv("CONFIG_PATH", "config.yaml"))
client = CssClient(config)
LOCAL_RECORDINGS_DIR = Path(os.getenv("LOCAL_RECORDINGS_DIR", "/mnt/nova_ssd/recordings"))


def normalize_id(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value


def ensure_sequence_videos(seq_dir):
    missing = []
    for view in CAMERA_VIEWS:
        video_path = seq_dir / f"{view}.mp4"
        if not video_path.exists():
            missing.append(f"{view}.mp4")

    if not missing:
        return []

    if os.getenv("AUTO_EXTRACT_MCAP", "0") != "1":
        return missing

    mcap_files = sorted(seq_dir.glob("*.mcap"))
    if not mcap_files:
        return missing

    print(f"Auto-extracting MP4s from MCAP for sequence: {seq_dir.name}")

    cmd = ["python", "extract_mcap_videos.py", str(seq_dir)]

    env = os.environ.copy()
    max_frames = os.getenv("MAX_FRAMES")
    if max_frames:
        env["MAX_FRAMES"] = max_frames

    subprocess.run(cmd, check=True, env=env)

    missing_after = []
    for view in CAMERA_VIEWS:
        video_path = seq_dir / f"{view}.mp4"
        if not video_path.exists():
            missing_after.append(f"{view}.mp4")

    return missing_after




HTML = """
<!doctype html>
<html>
<head>
  <title>Orin Multi-view Pre-label Tool</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #f4f4f4; }
    .topbar { height: 56px; background: #202020; color: white; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; }
    .layout { display: flex; gap: 24px; padding: 24px; }
    .sidebar, .main { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 5px rgba(0,0,0,0.15); }
    .sidebar { width: 380px; }
    .main { flex: 1; }
    label { display: block; margin-top: 14px; font-weight: bold; }
    input, textarea, select { width: 100%; box-sizing: border-box; padding: 9px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }
    textarea { min-height: 80px; }
    button { padding: 8px 12px; cursor: pointer; }
    .submit-btn { background: #76b900; color: white; border: none; padding: 10px 18px; border-radius: 4px; font-weight: bold; cursor: pointer; }
    .submit-btn:disabled { background: #777; cursor: not-allowed; }
    .valid { color: green; font-size: 13px; }
    .invalid { color: #b00020; font-size: 13px; }
    .view-status { margin-top: 8px; padding: 8px; background: #eeeeee; border-radius: 4px; font-size: 14px; }
    .complete { color: green; font-weight: bold; }
    .missing { color: #b00020; font-weight: bold; }
    .sequence-card { background: white; margin-bottom: 12px; padding: 14px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.12); }
    #videoWrap { position: relative; width: 900px; max-width: 100%; background: black; display: inline-block; line-height: 0; }
    #video { width: 100%; display: block; }
    #bboxCanvas { position: absolute; left: 0; top: 0; cursor: crosshair; z-index: 5; }
    .controls { margin-top: 12px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    #seek { width: 420px; }
    #status { margin-top: 16px; background: #eeeeee; padding: 10px; white-space: pre-wrap; max-height: 260px; overflow: auto; font-size: 13px; }
    .hint { color: #666; font-size: 14px; }
  </style>
</head>

<body>
  <div class="topbar">
    <div>
      <strong>Orin Multi-view Pre-label Tool</strong>
      <span id="sequenceTitle" style="margin-left: 16px;"></span>
    </div>
    <button id="submitBtn" class="submit-btn" onclick="submitMetadata()" disabled style="display:none;">Submit</button>
  </div>

  <div id="listingPage" style="padding:24px;">
    <h2>Sequences needing pre-label</h2>
    <button onclick="loadSequences()">Update</button>
    <div id="sequenceList" style="margin-top:16px;"></div>
  </div>

  <div id="labelPage" class="layout" style="display:none;">
    <div class="sidebar">
      <button onclick="backToListing()">Back to sequence list</button>
      <h2>Metadata</h2>

      <label>calib_sequence</label>
      <input id="calib_sequence" placeholder="example_calib_sequence" oninput="validateForm()">
      <div id="calibCheck" class="invalid">Required</div>

      <label>object_id</label>
      <input id="object_id" placeholder="test_object" oninput="validateForm()">
      <div id="objectCheck" class="invalid">Required</div>

      <label>person_id</label>
      <input id="person_id" placeholder="person_1" oninput="validateForm()">
      <div id="personCheck" class="invalid">Required</div>

      <label>action_description</label>
      <textarea id="action_description" placeholder="short action description" oninput="validateForm()"></textarea>
      <div id="actionCheck" class="invalid">Required</div>

      <label>action_language</label>
      <textarea id="action_language" placeholder="person interacts with the object" oninput="validateForm()"></textarea>
      <div id="actionLanguageCheck" class="invalid">Required</div>

      <h3>Bounding boxes</h3>
      <div id="viewStatuses"></div>

      <button onclick="clearCurrentBox()" style="margin-top:12px;">Clear current view box</button>
      <pre id="status"></pre>
    </div>

    <div class="main">
      <h2>Camera View</h2>

      <label>Select camera view</label>
      <select id="cameraSelect" onchange="switchCameraView()">
        <option value="front_stereo_camera_left">front_stereo_camera_left</option>
        <option value="back_stereo_camera_left">back_stereo_camera_left</option>
        <option value="left_stereo_camera_left">left_stereo_camera_left</option>
        <option value="right_stereo_camera_left">right_stereo_camera_left</option>
      </select>

      <p class="hint">Select each camera, pause video, then drag on the video to draw one bounding box.</p>

      <div id="videoWrap">
        <video id="video"></video>
        <canvas id="bboxCanvas"></canvas>
      </div>

      <div class="controls">
        <button onclick="togglePlay()">Play/Pause</button>
        <button onclick="stepFrame(-1)">-1 frame</button>
        <button onclick="stepFrame(1)">+1 frame</button>
        <input id="seek" type="range" min="0" max="1000" value="0" oninput="seekVideo()">
        <span id="timeLabel">0.00s</span>
        <span id="frameLabel">frame 0</span>
      </div>

      <p class="hint">Frame index is estimated using 30 FPS.</p>
    </div>
  </div>

<script>
const FPS = 30;
const CAMERA_VIEWS = ["front_stereo_camera_left", "back_stereo_camera_left", "left_stereo_camera_left", "right_stereo_camera_left"];

const video = document.getElementById("video");
const canvas = document.getElementById("bboxCanvas");
const ctx = canvas.getContext("2d");

let selectedSequence = null;
let videoUrls = {};
let currentView = "front_stereo_camera_left";

let drawing = false;
let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;

let boxesByView = {
  front_stereo_camera_left: null,
  back_stereo_camera_left: null,
  left_stereo_camera_left: null,
  right_stereo_camera_left: null
};

async function loadSequences() {
  const res = await fetch("/api/sequences");
  const sequences = await res.json();

  const container = document.getElementById("sequenceList");
  container.innerHTML = "";

  if (sequences.length === 0) {
    container.innerHTML = "<p>No sequences found or none need pre-label.</p>";
    return;
  }

  for (const seq of sequences) {
    const div = document.createElement("div");
    div.className = "sequence-card";

    let status = "";
    if (seq.has_metadata) status = "Already has hoi_metadata.yaml";
    else if (seq.missing_videos.length > 0) status = "Missing videos: " + seq.missing_videos.join(", ");
    else status = "Ready";

    div.innerHTML = `
      <strong>${seq.sequence_name}</strong>
      <div>${status}</div>
      <button ${seq.ready ? "" : "disabled"} onclick="openSequence('${seq.sequence_name}')">Open</button>
    `;

    container.appendChild(div);
  }
}

async function openSequence(sequenceName) {
  selectedSequence = sequenceName;

  const res = await fetch("/api/sequences/" + sequenceName);
  const data = await res.json();

  videoUrls = data.videos;

  boxesByView = {
    front_stereo_camera_left: null,
    back_stereo_camera_left: null,
    left_stereo_camera_left: null,
    right_stereo_camera_left: null
  };

  currentView = "front_stereo_camera_left";
  document.getElementById("cameraSelect").value = currentView;

  document.getElementById("listingPage").style.display = "none";
  document.getElementById("labelPage").style.display = "flex";
  document.getElementById("submitBtn").style.display = "inline-block";
  document.getElementById("sequenceTitle").textContent = "Sequence: " + sequenceName;

  video.src = videoUrls[currentView];
  video.load();

  updateViewStatuses();
  validateForm();
  resizeCanvasToVideo();
}

function backToListing() {
  selectedSequence = null;
  video.pause();
  document.getElementById("listingPage").style.display = "block";
  document.getElementById("labelPage").style.display = "none";
  document.getElementById("submitBtn").style.display = "none";
  document.getElementById("sequenceTitle").textContent = "";
  loadSequences();
}

function switchCameraView() {
  currentView = document.getElementById("cameraSelect").value;
  video.pause();
  video.src = videoUrls[currentView];
  video.load();
  updateTimeLabels();
  resizeCanvasToVideo();
  draw();
}

function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }

function resizeCanvasToVideo() {
  const rect = video.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  canvas.style.width = rect.width + "px";
  canvas.style.height = rect.height + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function getCanvasPoint(event) {
  const rect = canvas.getBoundingClientRect();
  return { x: clamp(event.clientX - rect.left, 0, rect.width), y: clamp(event.clientY - rect.top, 0, rect.height) };
}

function makeBox(x1, y1, x2, y2) {
  return { x: Math.min(x1, x2), y: Math.min(y1, y2), width: Math.abs(x2 - x1), height: Math.abs(y2 - y1) };
}

function normalizeBox(box) {
  const rect = canvas.getBoundingClientRect();
  return { x: box.x / rect.width, y: box.y / rect.height, width: box.width / rect.width, height: box.height / rect.height };
}

function denormalizeBox(box) {
  const rect = canvas.getBoundingClientRect();
  return { x: box.x * rect.width, y: box.y * rect.height, width: box.width * rect.width, height: box.height * rect.height };
}

function draw() {
  const rect = canvas.getBoundingClientRect();
  ctx.clearRect(0, 0, rect.width, rect.height);

  let boxToDraw = null;
  if (drawing) boxToDraw = makeBox(startX, startY, currentX, currentY);
  else if (boxesByView[currentView]) boxToDraw = denormalizeBox(boxesByView[currentView]);

  if (boxToDraw) {
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#00ff00";
    ctx.fillStyle = "rgba(0, 255, 0, 0.18)";
    ctx.fillRect(boxToDraw.x, boxToDraw.y, boxToDraw.width, boxToDraw.height);
    ctx.strokeRect(boxToDraw.x, boxToDraw.y, boxToDraw.width, boxToDraw.height);
  }
}

canvas.addEventListener("pointerdown", function(event) {
  const point = getCanvasPoint(event);
  drawing = true;
  startX = point.x;
  startY = point.y;
  currentX = point.x;
  currentY = point.y;
  canvas.setPointerCapture(event.pointerId);
  requestAnimationFrame(draw);
});

canvas.addEventListener("pointermove", function(event) {
  if (!drawing) return;
  const point = getCanvasPoint(event);
  currentX = point.x;
  currentY = point.y;
  requestAnimationFrame(draw);
});

canvas.addEventListener("pointerup", function(event) {
  if (!drawing) return;

  const point = getCanvasPoint(event);
  currentX = point.x;
  currentY = point.y;
  drawing = false;

  const finalBox = makeBox(startX, startY, currentX, currentY);

  if (finalBox.width > 5 && finalBox.height > 5) {
    const normalized = normalizeBox(finalBox);
    const rect = canvas.getBoundingClientRect();
    const scaleX = video.videoWidth / rect.width;
    const scaleY = video.videoHeight / rect.height;

    boxesByView[currentView] = {
      frame_idx: Math.round(video.currentTime * FPS),

      // Normalized box used by the browser UI for redraw.
      x: normalized.x,
      y: normalized.y,
      width: normalized.width,
      height: normalized.height,

      // Pixel box used by backend export: labeled_bboxes/<camera>.json.
      x0: finalBox.x * scaleX,
      y0: finalBox.y * scaleY,
      x1: (finalBox.x + finalBox.width) * scaleX,
      y1: (finalBox.y + finalBox.height) * scaleY
    };
  }

  updateViewStatuses();
  validateForm();
  requestAnimationFrame(draw);
});

function clearCurrentBox() {
  boxesByView[currentView] = null;
  updateViewStatuses();
  validateForm();
  draw();
}

function togglePlay() {
  if (video.paused) video.play();
  else video.pause();
}

function stepFrame(direction) {
  video.pause();
  video.currentTime = Math.max(0, video.currentTime + direction / FPS);
  updateTimeLabels();
}

function seekVideo() {
  const seek = document.getElementById("seek");
  if (!video.duration) return;
  video.currentTime = Number(seek.value) / 1000 * video.duration;
  updateTimeLabels();
}

function updateTimeLabels() {
  const time = video.currentTime || 0;
  const frame = Math.round(time * FPS);
  document.getElementById("timeLabel").textContent = time.toFixed(2) + "s";
  document.getElementById("frameLabel").textContent = "frame " + frame;

  if (video.duration) {
    document.getElementById("seek").value = String((time / video.duration) * 1000);
  }
}

video.addEventListener("loadedmetadata", function() {
  resizeCanvasToVideo();
  updateTimeLabels();
});
video.addEventListener("timeupdate", updateTimeLabels);
window.addEventListener("resize", resizeCanvasToVideo);
new ResizeObserver(function() { resizeCanvasToVideo(); }).observe(video);

function getValue(id) { return document.getElementById(id).value.trim(); }

function setCheck(id, ok, message) {
  const el = document.getElementById(id);
  if (ok) { el.textContent = "✓ Complete"; el.className = "valid"; }
  else { el.textContent = message; el.className = "invalid"; }
}

function allViewsHaveBoxes() {
  return CAMERA_VIEWS.every(function(view) { return boxesByView[view] !== null; });
}

function updateViewStatuses() {
  const container = document.getElementById("viewStatuses");
  container.innerHTML = "";

  for (const view of CAMERA_VIEWS) {
    const div = document.createElement("div");
    div.className = "view-status";
    if (boxesByView[view]) div.innerHTML = '<span class="complete">✓</span> ' + view;
    else div.innerHTML = '<span class="missing">✗</span> ' + view;
    container.appendChild(div);
  }
}

function validateForm() {
  const calibOk = getValue("calib_sequence").length > 0;
  const objectOk = getValue("object_id").length > 0;
  const personOk = getValue("person_id").length > 0;
  const actionOk = getValue("action_description").length > 0;
  const actionLanguageOk = getValue("action_language").length > 0;
  const bboxOk = allViewsHaveBoxes();

  setCheck("calibCheck", calibOk, "Required");
  setCheck("objectCheck", objectOk, "Required");
  setCheck("personCheck", personOk, "Required");
  setCheck("actionCheck", actionOk, "Required");
  setCheck("actionLanguageCheck", actionLanguageOk, "Required");

  document.getElementById("submitBtn").disabled = !(calibOk && objectOk && personOk && actionOk && actionLanguageOk && bboxOk);
}

async function submitMetadata() {
  const payload = {
    sequence_name: selectedSequence,
    location: "sc_office_4exo_1",
    calib_sequence: getValue("calib_sequence"),
    object_id: getValue("object_id").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, ""),
    person_id: getValue("person_id").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, ""),
    action_description: getValue("action_description"),
    action_language: getValue("action_language"),
    per_view_bounding_boxes: boxesByView
  };

  const res = await fetch("/api/sequences/" + selectedSequence + "/submit", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  document.getElementById("status").textContent = JSON.stringify(data, null, 2);

  if (data.ok) {
    document.getElementById("submitBtn").disabled = true;
    setTimeout(function() {
      backToListing();
    }, 1000);
  }
}

loadSequences();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/sequences")
def api_sequences():
    sequence_filter = request.args.get("sequence") or os.getenv("SEQUENCE_NAME")

    results = []

    if not LOCAL_RECORDINGS_DIR.exists():
        return jsonify([])

    for seq_dir in sorted(LOCAL_RECORDINGS_DIR.iterdir()):
        if not seq_dir.is_dir():
            continue

        sequence_name = seq_dir.name

        if sequence_filter and sequence_name != sequence_filter:
            continue

        missing_videos = ensure_sequence_videos(seq_dir)

        # Local/Orin workflow: avoid remote HeadObject during listing.
        # A sequence is complete locally if hoi_metadata.yaml or marker exists.
        has_metadata = (seq_dir / "hoi_metadata.yaml").exists() or (seq_dir / ".prelabel_uploaded").exists()

        ready = len(missing_videos) == 0 and not has_metadata

        results.append({
            "sequence_name": sequence_name,
            "location": client.location,
            "missing_videos": missing_videos,
            "has_metadata": has_metadata,
            "ready": ready,
        })

    needing_prelabel = [s for s in results if s["ready"]]

    # One-at-a-time mode.
    if os.getenv("ONE_AT_A_TIME", "1") == "1":
        needing_prelabel = needing_prelabel[:1]

    return jsonify(needing_prelabel)


@app.route("/api/sequences/<sequence_name>")
def api_sequence(sequence_name):
    videos = {}
    for view in CAMERA_VIEWS:
        videos[view] = f"/local_video/{sequence_name}/{view}.mp4"

    return jsonify({
        "sequence_name": sequence_name,
        "location": client.location,
        "videos": videos,
    })


@app.route("/local_video/<sequence_name>/<filename>")
def local_video(sequence_name, filename):
    # Basic path safety.
    if "/" in sequence_name or ".." in sequence_name or "/" in filename or ".." in filename:
        abort(400)

    video_path = LOCAL_RECORDINGS_DIR / sequence_name / filename

    if not video_path.exists():
        abort(404)

    return send_file(video_path)




def utc_now_str():
    return str(datetime.now(timezone.utc))


def build_hoi_metadata(payload, sequence_name):
    """
    New hoi_metadata.yaml format.

    object.bbox and object.prompt are intentionally NOT written here.
    Bboxes are written separately to labeled_bboxes/<camera_view>.json.
    """
    return {
        "action_desc": payload.get("action_description", ""),
        "calib_seq_name": payload.get("calib_sequence", ""),
        "object": {
            "id": payload.get("object_id", ""),
        },
        "person": {
            "id": payload.get("person_id", ""),
        },
        "record_datetime": payload.get("record_datetime") or utc_now_str(),
        "rig": payload.get("rig", "nova_hawk"),
        "rig_name": payload.get("location", client.location),
        "session_id": sequence_name,
        "upload_datetime": utc_now_str(),
    }


def bbox_to_xyxy(raw_box):
    """
    Convert current frontend bbox format to required x0/y0/x1/y1 format.
    """

    if raw_box is None:
        raise ValueError("Missing bbox")

    if "box" in raw_box and isinstance(raw_box["box"], dict):
        raw_box = raw_box["box"]

    if all(k in raw_box for k in ("x0", "y0", "x1", "y1")):
        return {
            "x0": float(raw_box["x0"]),
            "y0": float(raw_box["y0"]),
            "x1": float(raw_box["x1"]),
            "y1": float(raw_box["y1"]),
        }

    if all(k in raw_box for k in ("x", "y", "w", "h")):
        x = float(raw_box["x"])
        y = float(raw_box["y"])
        w = float(raw_box["w"])
        h = float(raw_box["h"])
        return {
            "x0": x,
            "y0": y,
            "x1": x + w,
            "y1": y + h,
        }

    if all(k in raw_box for k in ("x", "y", "width", "height")):
        x = float(raw_box["x"])
        y = float(raw_box["y"])
        w = float(raw_box["width"])
        h = float(raw_box["height"])
        return {
            "x0": x,
            "y0": y,
            "x1": x + w,
            "y1": y + h,
        }

    if all(k in raw_box for k in ("left", "top", "width", "height")):
        x = float(raw_box["left"])
        y = float(raw_box["top"])
        w = float(raw_box["width"])
        h = float(raw_box["height"])
        return {
            "x0": x,
            "y0": y,
            "x1": x + w,
            "y1": y + h,
        }

    raise ValueError(f"Unsupported bbox format: {raw_box}")


def bbox_frame_idx(raw_box):
    """
    Frame index is stored as a 6-digit string key in the JSON output.
    """
    if raw_box is None:
        return 0

    for key in ("frame_idx", "frameIndex", "frame"):
        if key in raw_box and raw_box[key] is not None:
            return int(raw_box[key])

    return 0


def write_labeled_bbox_files(seq_dir, payload):
    """
    Writes one bbox JSON file per camera view:

      labeled_bboxes/<camera_view>.json

    Format:

      {
        "000000": [
          {
            "label": "blue_trash_can",
            "box": {
              "x0": ...,
              "y0": ...,
              "x1": ...,
              "y1": ...
            }
          }
        ]
      }
    """
    label = payload.get("object_id", "")
    per_view_boxes = payload.get("per_view_bounding_boxes") or {}

    output_dir = seq_dir / "labeled_bboxes"
    output_dir.mkdir(parents=True, exist_ok=True)

    written_paths = []

    for view, raw_box in per_view_boxes.items():
        if raw_box is None:
            continue

        frame_idx = bbox_frame_idx(raw_box)
        frame_key = f"{frame_idx:06d}"

        output = {
            frame_key: [
                {
                    "label": label,
                    "box": bbox_to_xyxy(raw_box),
                }
            ]
        }

        output_path = output_dir / f"{view}.json"

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        written_paths.append(output_path)

    return written_paths

@app.route("/api/sequences/<sequence_name>/submit", methods=["POST"])
def api_submit(sequence_name):
    payload = request.get_json()

    payload["sequence_name"] = sequence_name
    payload["location"] = client.location
    payload["object_id"] = normalize_id(payload.get("object_id", ""))
    payload["person_id"] = normalize_id(payload.get("person_id", ""))

    seq_dir = LOCAL_RECORDINGS_DIR / sequence_name

    if not seq_dir.exists():
        return jsonify({"ok": False, "error": f"Missing local sequence folder: {seq_dir}"}), 404

    hoi_metadata = build_hoi_metadata(payload, sequence_name)

    try:
        bbox_paths = write_labeled_bbox_files(seq_dir, payload)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to write labeled bbox files: {e}"}), 400

    uploaded_videos = []
    uploaded_bboxes = []

    # Upload videos first.
    for view in CAMERA_VIEWS:
        filename = f"{view}.mp4"
        local_path = seq_dir / filename

        if not local_path.exists():
            return jsonify({"ok": False, "error": f"Missing local video: {local_path}"}), 400

        key = client.upload_file(local_path, sequence_name, filename)
        uploaded_videos.append(f"s3://{client.bucket}/{key}")

    # Upload bbox JSON files before metadata.
    for bbox_path in bbox_paths:
        relative_name = bbox_path.relative_to(seq_dir).as_posix()
        key = client.upload_file(bbox_path, sequence_name, relative_name)
        uploaded_bboxes.append(f"s3://{client.bucket}/{key}")

    # Upload metadata last, so metadata means sequence is complete.
    yaml_text = yaml.safe_dump(hoi_metadata, sort_keys=False)
    metadata_key = client.upload_yaml_text(sequence_name, yaml_text)

    # Save local completion marker so this sequence disappears from ready list.
    (seq_dir / "hoi_metadata.yaml").write_text(yaml_text)
    (seq_dir / ".prelabel_uploaded").write_text(metadata_key + "\n")

    return jsonify({
        "ok": True,
        "uploaded_to": f"s3://{client.bucket}/{metadata_key}",
        "uploaded_videos": uploaded_videos,
        "uploaded_bboxes": uploaded_bboxes,
        "metadata": hoi_metadata,
    })


if __name__ == "__main__":
    if "multiview_test" not in client.base_prefix and os.getenv("ALLOW_PROD_UPLOAD") != "1":
        raise SystemExit(f"Refusing to upload outside test prefix: {client.base_prefix}. Set ALLOW_PROD_UPLOAD=1 if intentional.")

    print("Using CSS/PDX upload prefix:")
    print(f"  bucket: {client.bucket}")
    print(f"  prefix: {client.base_prefix}")

    url = "http://127.0.0.1:8000"
    print(f"Opening {url}")


    if os.getenv("AUTO_OPEN_BROWSER", "1") == "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(debug=True, port=8000, use_reloader=False)
