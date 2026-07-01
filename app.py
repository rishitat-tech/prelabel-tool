from flask import Flask, send_file, render_template_string, request, jsonify
import os
import re
import yaml

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEQUENCE_NAME = "sample_sequence"
LOCATION = "sc_office_4exo_1"

VIDEO_DIR = os.path.join(BASE_DIR, "videos", SEQUENCE_NAME)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "hoi_metadata.yaml")

os.makedirs(OUTPUT_DIR, exist_ok=True)

CAMERA_VIEWS = [
    "front_stereo_camera_left",
    "back_stereo_camera_left",
    "left_stereo_camera_left",
    "right_stereo_camera_left",
]


def normalize_object_id(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value


HTML = """
<!doctype html>
<html>
<head>
  <title>Multi-view Pre-label Tool</title>
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f4f4f4;
    }

    .topbar {
      height: 56px;
      background: #202020;
      color: white;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
    }

    .layout {
      display: flex;
      gap: 24px;
      padding: 24px;
    }

    .sidebar {
      width: 360px;
      background: white;
      padding: 20px;
      border-radius: 8px;
    }

    .main {
      flex: 1;
      background: white;
      padding: 20px;
      border-radius: 8px;
    }

    label {
      display: block;
      margin-top: 14px;
      font-weight: bold;
    }

    input, textarea, select {
      width: 100%;
      box-sizing: border-box;
      padding: 9px;
      margin-top: 5px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }

    textarea {
      min-height: 80px;
    }

    .submit-btn {
      background: #76b900;
      color: white;
      border: none;
      padding: 10px 18px;
      border-radius: 4px;
      font-weight: bold;
      cursor: pointer;
    }

    .submit-btn:disabled {
      background: #777;
      cursor: not-allowed;
    }

    .valid {
      color: green;
      font-size: 13px;
    }

    .invalid {
      color: #b00020;
      font-size: 13px;
    }

    .view-status {
      margin-top: 8px;
      padding: 8px;
      background: #eeeeee;
      border-radius: 4px;
      font-size: 14px;
    }

    .complete {
      color: green;
      font-weight: bold;
    }

    .missing {
      color: #b00020;
      font-weight: bold;
    }

    #videoWrap {
      position: relative;
      width: 900px;
      max-width: 100%;
      background: black;
      display: inline-block;
      line-height: 0;
    }

    #video {
      width: 100%;
      display: block;
    }

    #bboxCanvas {
      position: absolute;
      left: 0;
      top: 0;
      cursor: crosshair;
      z-index: 5;
    }

    .controls {
      margin-top: 12px;
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }

    .controls button {
      padding: 8px 12px;
      cursor: pointer;
    }

    #seek {
      width: 420px;
    }

    #status {
      margin-top: 16px;
      background: #eeeeee;
      padding: 10px;
      white-space: pre-wrap;
      max-height: 260px;
      overflow: auto;
      font-size: 13px;
    }

    .hint {
      color: #666;
      font-size: 14px;
    }
  </style>
</head>

<body>
  <div class="topbar">
    <div>
      <strong>Multi-view Pre-label Tool</strong>
      <span style="margin-left: 16px;">Sequence: sample_sequence</span>
    </div>

    <button id="submitBtn" class="submit-btn" onclick="submitMetadata()" disabled>
      Submit
    </button>
  </div>

  <div class="layout">
    <div class="sidebar">
      <h2>Metadata</h2>

      <label>calib_sequence</label>
      <input id="calib_sequence" placeholder="example_calib_sequence" oninput="validateForm()">
      <div id="calibCheck" class="invalid">Required</div>

      <label>object_id</label>
      <input id="object_id" placeholder="Blue Easter Basket" oninput="validateForm()">
      <div id="objectCheck" class="invalid">Required</div>

      <label>action_description</label>
      <textarea id="action_description" placeholder="Pick and place object" oninput="validateForm()"></textarea>
      <div id="actionCheck" class="invalid">Required</div>

      <label>person_id</label>
      <input id="person_id" placeholder="person_1" oninput="validateForm()">
      <div id="personCheck" class="invalid">Required</div>

      <label>action_language</label>
      <textarea id="action_language" placeholder="person picks up the object from the table" oninput="validateForm()"></textarea>
      <div id="actionLanguageCheck" class="invalid">Required</div>

      <h3>Bounding boxes</h3>
      <div id="viewStatuses"></div>

      <button onclick="clearCurrentBox()" style="margin-top: 12px; padding: 8px 12px;">
        Clear current view box
      </button>

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

      <p class="hint">
        Select each camera, pause the video, then drag on the video to draw one bounding box.
      </p>

      <div id="videoWrap">
        <video id="video" src="/video/front_stereo_camera_left"></video>
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

const CAMERA_VIEWS = [
  "front_stereo_camera_left",
  "back_stereo_camera_left",
  "left_stereo_camera_left",
  "right_stereo_camera_left"
];

const video = document.getElementById("video");
const canvas = document.getElementById("bboxCanvas");
const ctx = canvas.getContext("2d");

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

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

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

  return {
    x: clamp(event.clientX - rect.left, 0, rect.width),
    y: clamp(event.clientY - rect.top, 0, rect.height)
  };
}

function makeBox(x1, y1, x2, y2) {
  return {
    x: Math.min(x1, x2),
    y: Math.min(y1, y2),
    width: Math.abs(x2 - x1),
    height: Math.abs(y2 - y1)
  };
}

function normalizeBox(box) {
  const rect = canvas.getBoundingClientRect();

  return {
    x: box.x / rect.width,
    y: box.y / rect.height,
    width: box.width / rect.width,
    height: box.height / rect.height
  };
}

function denormalizeBox(box) {
  const rect = canvas.getBoundingClientRect();

  return {
    x: box.x * rect.width,
    y: box.y * rect.height,
    width: box.width * rect.width,
    height: box.height * rect.height
  };
}

function draw() {
  const rect = canvas.getBoundingClientRect();
  ctx.clearRect(0, 0, rect.width, rect.height);

  let boxToDraw = null;

  if (drawing) {
    boxToDraw = makeBox(startX, startY, currentX, currentY);
  } else if (boxesByView[currentView]) {
    boxToDraw = denormalizeBox(boxesByView[currentView]);
  }

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

    boxesByView[currentView] = {
      frame_idx: Math.round(video.currentTime * FPS),
      x: normalized.x,
      y: normalized.y,
      width: normalized.width,
      height: normalized.height
    };
  }

  updateViewStatuses();
  validateForm();
  requestAnimationFrame(draw);
});

function switchCameraView() {
  currentView = document.getElementById("cameraSelect").value;

  video.pause();

  // cache-buster forces browser to load the selected camera file
  video.src = "/video/" + currentView + "?t=" + Date.now();
  video.load();

  updateTimeLabels();
  resizeCanvasToVideo();
  draw();
}

function clearCurrentBox() {
  boxesByView[currentView] = null;
  updateViewStatuses();
  validateForm();
  draw();
}

function togglePlay() {
  if (video.paused) {
    video.play();
  } else {
    video.pause();
  }
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
  } else {
    document.getElementById("seek").value = "0";
  }
}

video.addEventListener("loadedmetadata", function() {
  resizeCanvasToVideo();
  updateTimeLabels();
});

video.addEventListener("timeupdate", updateTimeLabels);
window.addEventListener("resize", resizeCanvasToVideo);

const resizeObserver = new ResizeObserver(function() {
  resizeCanvasToVideo();
});

resizeObserver.observe(video);

function getValue(id) {
  return document.getElementById(id).value.trim();
}

function setCheck(id, ok, message) {
  const el = document.getElementById(id);

  if (ok) {
    el.textContent = "✓ Complete";
    el.className = "valid";
  } else {
    el.textContent = message;
    el.className = "invalid";
  }
}

function allViewsHaveBoxes() {
  return CAMERA_VIEWS.every(function(view) {
    return boxesByView[view] !== null;
  });
}

function updateViewStatuses() {
  const container = document.getElementById("viewStatuses");
  container.innerHTML = "";

  for (const view of CAMERA_VIEWS) {
    const div = document.createElement("div");
    div.className = "view-status";

    if (boxesByView[view]) {
      div.innerHTML = '<span class="complete">✓</span> ' + view;
    } else {
      div.innerHTML = '<span class="missing">✗</span> ' + view;
    }

    container.appendChild(div);
  }
}

function validateForm() {
  const calibOk = getValue("calib_sequence").length > 0;
  const objectOk = getValue("object_id").length > 0;
  const actionOk = getValue("action_description").length > 0;
  const personOk = getValue("person_id").length > 0;
  const actionLanguageOk = getValue("action_language").length > 0;
  const bboxOk = allViewsHaveBoxes();

  setCheck("calibCheck", calibOk, "Required");
  setCheck("objectCheck", objectOk, "Required");
  setCheck("actionCheck", actionOk, "Required");
  setCheck("personCheck", personOk, "Required");
  setCheck("actionLanguageCheck", actionLanguageOk, "Required");

  document.getElementById("submitBtn").disabled = !(
    calibOk &&
    objectOk &&
    actionOk &&
    personOk &&
    actionLanguageOk &&
    bboxOk
  );
}

async function submitMetadata() {
  const payload = {
    sequence_name: "sample_sequence",
    location: "sc_office_4exo_1",
    calib_sequence: getValue("calib_sequence"),
    object_id: getValue("object_id")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, ""),
    person_id: getValue("person_id")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, ""),
    action_description: getValue("action_description"),
    action_language: getValue("action_language"),
    per_view_bounding_boxes: boxesByView
  };

  const res = await fetch("/submit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  document.getElementById("status").textContent = JSON.stringify(data, null, 2);
}

updateViewStatuses();
validateForm();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/video/<camera_view>")
def video(camera_view):
    if camera_view not in CAMERA_VIEWS:
        return f"Unknown camera view: {camera_view}", 404

    video_path = os.path.join(VIDEO_DIR, f"{camera_view}.mp4")

    if not os.path.exists(video_path):
        return f"Missing video: {video_path}", 404

    return send_file(video_path, mimetype="video/mp4", conditional=True)


@app.route("/submit", methods=["POST"])
def submit():
    payload = request.get_json()
    payload["object_id"] = normalize_object_id(payload.get("object_id", ""))

    with open(OUTPUT_PATH, "w") as f:
        yaml.safe_dump(payload, f, sort_keys=False)

    return jsonify({
        "ok": True,
        "saved_to": OUTPUT_PATH,
        "metadata": payload
    })


if __name__ == "__main__":
    app.run(debug=True, port=8000)
