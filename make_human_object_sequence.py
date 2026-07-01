import os
import sys
import imageio.v3 as iio
import numpy as np

sequence_name = sys.argv[1] if len(sys.argv) > 1 else "test_human_object_001"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos", sequence_name)
os.makedirs(VIDEO_DIR, exist_ok=True)

WIDTH = 1280
HEIGHT = 720
FPS = 30
NUM_FRAMES = 180

CAMERAS = {
    "front_stereo_camera_left": [35, 35, 35],
    "back_stereo_camera_left": [45, 35, 30],
    "left_stereo_camera_left": [30, 40, 50],
    "right_stereo_camera_left": [45, 30, 50],
}


def draw_rect(frame, x1, y1, x2, y2, color):
    x1 = max(0, min(WIDTH - 1, int(x1)))
    x2 = max(0, min(WIDTH, int(x2)))
    y1 = max(0, min(HEIGHT - 1, int(y1)))
    y2 = max(0, min(HEIGHT, int(y2)))
    if x2 > x1 and y2 > y1:
        frame[y1:y2, x1:x2] = color


def draw_circle(frame, cx, cy, r, color):
    yy, xx = np.ogrid[:HEIGHT, :WIDTH]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2
    frame[mask] = color


def make_video(camera_name, bg_color, view_shift):
    frames = []

    for i in range(NUM_FRAMES):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        frame[:, :] = bg_color

        # floor/table
        draw_rect(frame, 0, 520, WIDTH, HEIGHT, [80, 80, 80])
        draw_rect(frame, 250, 430, 1030, 530, [120, 95, 60])

        # grid for visual difference
        for x in range(0, WIDTH, 100):
            draw_rect(frame, x, 0, x + 2, HEIGHT, [55, 55, 55])
        for y in range(0, HEIGHT, 100):
            draw_rect(frame, 0, y, WIDTH, y + 2, [55, 55, 55])

        # synthetic human position
        person_x = 420 + view_shift
        person_y = 250

        # head
        draw_circle(frame, person_x, person_y, 45, [230, 190, 150])

        # body
        draw_rect(frame, person_x - 45, person_y + 50, person_x + 45, person_y + 190, [40, 120, 220])

        # legs
        draw_rect(frame, person_x - 40, person_y + 190, person_x - 10, person_y + 320, [30, 30, 160])
        draw_rect(frame, person_x + 10, person_y + 190, person_x + 40, person_y + 320, [30, 30, 160])

        # moving arm reaching object
        reach = min(1.0, i / 90.0)
        arm_end_x = int(person_x + 80 + 220 * reach)
        arm_end_y = int(person_y + 115)

        # arm as thick line approximation
        x_start = person_x + 45
        y_start = person_y + 100
        steps = 50
        for s in range(steps):
            t = s / steps
            x = int(x_start * (1 - t) + arm_end_x * t)
            y = int(y_start * (1 - t) + arm_end_y * t)
            draw_circle(frame, x, y, 8, [230, 190, 150])

        # object: green box on table
        obj_x = 730 + view_shift // 3
        obj_y = 390
        draw_rect(frame, obj_x, obj_y, obj_x + 140, obj_y + 100, [0, 200, 80])

        # object outline
        draw_rect(frame, obj_x, obj_y, obj_x + 140, obj_y + 5, [0, 0, 0])
        draw_rect(frame, obj_x, obj_y + 95, obj_x + 140, obj_y + 100, [0, 0, 0])
        draw_rect(frame, obj_x, obj_y, obj_x + 5, obj_y + 100, [0, 0, 0])
        draw_rect(frame, obj_x + 135, obj_y, obj_x + 140, obj_y + 100, [0, 0, 0])

        frames.append(frame)

    out_path = os.path.join(VIDEO_DIR, f"{camera_name}.mp4")
    iio.imwrite(
        out_path,
        frames,
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
    )
    print(f"Created {out_path}")


make_video("front_stereo_camera_left", CAMERAS["front_stereo_camera_left"], 0)
make_video("back_stereo_camera_left", CAMERAS["back_stereo_camera_left"], 80)
make_video("left_stereo_camera_left", CAMERAS["left_stereo_camera_left"], -120)
make_video("right_stereo_camera_left", CAMERAS["right_stereo_camera_left"], 140)

print(f"Done: videos/{sequence_name}")
