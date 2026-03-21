"""
Evaluate trained LSTM fall detector on keypoint CSV dataset.

Usage:
  python scripts/evaluate_lstm.py
"""

from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import tensorflow as tf

SEQUENCE_LENGTH = 30
NUM_FEATURES = 66
BASE_DIR = Path(__file__).resolve().parent.parent
KEYPOINTS_DIR = BASE_DIR / "data" / "keypoints"
MODEL_PATH = BASE_DIR / "models" / "fall_lstm.keras"
SCALER_PATH = BASE_DIR / "models" / "fall_lstm_scaler.pkl"
REPORT_PATH = BASE_DIR / "models" / "lstm_eval_report.txt"


def load_sequences(keypoints_dir: Path):
    X, y = [], []
    csv_files = sorted([p for p in keypoints_dir.iterdir() if p.suffix == ".csv"])
    for csv_path in csv_files:
        df = pd.read_csv(csv_path)
        if "label" not in df.columns:
            continue
        label = int(df["label"].iloc[0])
        features = df.drop(columns=["label"]).values.astype(np.float32)
        n_frames = len(features)
        if n_frames == 0:
            continue

        if n_frames < SEQUENCE_LENGTH:
            pad = np.tile(features[-1], (SEQUENCE_LENGTH - n_frames, 1))
            seq = np.vstack([features, pad])
            X.append(seq)
            y.append(label)
        else:
            step = SEQUENCE_LENGTH // 2
            for start in range(0, n_frames - SEQUENCE_LENGTH + 1, step):
                X.append(features[start:start + SEQUENCE_LENGTH])
                y.append(label)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing model: {MODEL_PATH}")
    if not SCALER_PATH.exists():
        raise FileNotFoundError(f"Missing scaler: {SCALER_PATH}")

    X, y = load_sequences(KEYPOINTS_DIR)
    if len(X) == 0:
        raise RuntimeError(f"No keypoint sequences found in {KEYPOINTS_DIR}")

    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    n_samples, seq_len, n_feat = X.shape
    if n_feat != NUM_FEATURES or seq_len != SEQUENCE_LENGTH:
        raise RuntimeError(f"Unexpected shape: {X.shape}, expected (*, {SEQUENCE_LENGTH}, {NUM_FEATURES})")

    X_flat = X.reshape(-1, n_feat)
    X_flat = scaler.transform(X_flat)
    X = X_flat.reshape(n_samples, seq_len, n_feat)

    model = tf.keras.models.load_model(MODEL_PATH)
    probs = model.predict(X, verbose=0).flatten()
    preds = (probs >= 0.5).astype(np.int32)

    acc = accuracy_score(y, preds)
    cm = confusion_matrix(y, preds)
    report = classification_report(y, preds, target_names=["ADL", "Fall"], digits=4)

    lines = [
        "LSTM Fall Detection Evaluation",
        "=" * 40,
        f"Samples: {len(X)}",
        f"Accuracy: {acc:.4f}",
        "",
        "Confusion Matrix [ADL, Fall]:",
        str(cm),
        "",
        "Classification Report:",
        report,
    ]
    text = "\n".join(lines)
    REPORT_PATH.write_text(text)
    print(text)
    print(f"\nSaved report to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
