"""
Step 2: Extract pose keypoints from URFD videos using MediaPipe Tasks API.

For each video:
- Runs MediaPipe Pose Landmarker on every frame
- Extracts 33 body keypoints (x, y per point = 66 numbers per frame)
- Saves each video as a CSV sequence
- Labels: fall = 1, ADL = 0

Output saved to: data/keypoints/
"""

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALL_DIR   = os.path.join(BASE_DIR, "data", "urfd", "Fall")
ADL_DIR    = os.path.join(BASE_DIR, "data", "urfd", "Activities of Daily Living")
OUT_DIR    = os.path.join(BASE_DIR, "data", "keypoints")
MODEL_PATH = os.path.join(BASE_DIR, "models", "pose_landmarker.task")

os.makedirs(OUT_DIR, exist_ok=True)

# ── MediaPipe Tasks API setup ──────────────────────────────────────────────────
BaseOptions          = mp.tasks.BaseOptions
PoseLandmarker       = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode    = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.IMAGE,
)

NUM_KEYPOINTS = 33


def extract_keypoints_from_video(video_path, landmarker):
    """
    Read a video file frame by frame.
    For each frame, extract 33 keypoints (x, y) = 66 numbers.
    Returns a list of frames, each frame is a flat array of 66 floats.
    """
    cap      = cv2.VideoCapture(video_path)
    sequence = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result   = landmarker.detect(mp_image)

        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            keypoints = []
            for landmark in result.pose_landmarks[0]:
                keypoints.append(landmark.x)
                keypoints.append(landmark.y)
            sequence.append(keypoints)
        else:
            # No person detected — fill with zeros to keep sequence intact
            sequence.append([0.0] * (NUM_KEYPOINTS * 2))

    cap.release()
    return sequence if len(sequence) > 0 else None


def process_folder(folder_path, label, label_name, landmarker):
    """Process all videos in a folder and save each as a CSV."""
    videos  = sorted([f for f in os.listdir(folder_path) if f.endswith(".mp4")])
    print(f"\nProcessing {label_name} videos ({len(videos)} files)...")

    saved   = 0
    skipped = 0

    for video_file in videos:
        video_path = os.path.join(folder_path, video_file)
        name       = os.path.splitext(video_file)[0]
        out_path   = os.path.join(OUT_DIR, f"{name}.csv")

        print(f"  [{label_name}] {video_file} ...", end=" ", flush=True)

        sequence = extract_keypoints_from_video(video_path, landmarker)

        if sequence is None or len(sequence) == 0:
            print("SKIPPED (no frames)")
            skipped += 1
            continue

        columns = []
        for i in range(NUM_KEYPOINTS):
            columns.append(f"kp{i}_x")
            columns.append(f"kp{i}_y")

        df          = pd.DataFrame(sequence, columns=columns)
        df["label"] = label  # 1 = fall, 0 = adl

        df.to_csv(out_path, index=False)
        print(f"done ({len(sequence)} frames)")
        saved += 1

    print(f"  {label_name}: {saved} saved, {skipped} skipped")
    return saved


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("URFD Keypoint Extraction")
    print("=" * 60)
    print(f"Fall videos  : {FALL_DIR}")
    print(f"ADL videos   : {ADL_DIR}")
    print(f"Output folder: {OUT_DIR}")
    print(f"Model        : {MODEL_PATH}")

    with PoseLandmarker.create_from_options(options) as landmarker:
        fall_count = process_folder(FALL_DIR, label=1, label_name="FALL", landmarker=landmarker)
        adl_count  = process_folder(ADL_DIR,  label=0, label_name="ADL",  landmarker=landmarker)

    print("\n" + "=" * 60)
    print(f"Done! {fall_count} fall CSVs + {adl_count} ADL CSVs saved to:")
    print(f"  {OUT_DIR}")
    print("=" * 60)
    print("\nNext step: run train_lstm.py to train the fall detection model.")
