"""
Step 3: Train LSTM model on extracted keypoints from URFD dataset.

Input : data/keypoints/*.csv  (70 CSV files — 30 falls, 40 ADL)
Output: models/fall_lstm.keras  (trained model)
        models/fall_lstm_scaler.pkl (feature scaler)

Each CSV has 66 keypoint columns (x,y for 33 landmarks) + 1 label column.
Sequences are padded/truncated to SEQUENCE_LENGTH frames.
"""

import os
import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# ── Config ─────────────────────────────────────────────────────────────────────
SEQUENCE_LENGTH = 30        # frames per sequence fed into LSTM
NUM_FEATURES    = 66        # 33 keypoints × 2 (x, y)
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYPOINTS_DIR   = os.path.join(BASE_DIR, "data", "keypoints")
MODELS_DIR      = os.path.join(BASE_DIR, "models")
MODEL_PATH      = os.path.join(MODELS_DIR, "fall_lstm.keras")
SCALER_PATH     = os.path.join(MODELS_DIR, "fall_lstm_scaler.pkl")


def load_sequences(keypoints_dir):
    """
    Load all CSV files and convert each into fixed-length sequences.
    Each video → one or more sequences of SEQUENCE_LENGTH frames.
    Returns X (samples, SEQUENCE_LENGTH, NUM_FEATURES) and y (samples,).
    """
    X, y = [], []
    csv_files = sorted([f for f in os.listdir(keypoints_dir) if f.endswith(".csv")])

    print(f"Loading {len(csv_files)} CSV files...")

    for csv_file in csv_files:
        path  = os.path.join(keypoints_dir, csv_file)
        df    = pd.read_csv(path)
        label = int(df["label"].iloc[0])  # 1=fall, 0=adl

        features = df.drop(columns=["label"]).values.astype(np.float32)
        n_frames = len(features)

        if n_frames < SEQUENCE_LENGTH:
            # Pad short videos by repeating the last frame
            pad    = np.tile(features[-1], (SEQUENCE_LENGTH - n_frames, 1))
            seq    = np.vstack([features, pad])
            X.append(seq)
            y.append(label)
        else:
            # Slide a window across longer videos — creates more training samples
            step = SEQUENCE_LENGTH // 2
            for start in range(0, n_frames - SEQUENCE_LENGTH + 1, step):
                X.append(features[start : start + SEQUENCE_LENGTH])
                y.append(label)

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    print(f"  Total sequences: {len(X)}  (falls: {y.sum()}, normal: {(y==0).sum()})")
    return X, y


def build_lstm_model(sequence_length, num_features):
    """Build a 2-layer LSTM classifier."""
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(sequence_length, num_features)),
        BatchNormalization(),
        Dropout(0.3),

        LSTM(32, return_sequences=False),
        BatchNormalization(),
        Dropout(0.3),

        Dense(16, activation="relu"),
        Dense(1,  activation="sigmoid"),  # binary: fall or not
    ])

    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("LSTM Fall Detection — Training")
    print("=" * 60)

    # 1. Load data
    X, y = load_sequences(KEYPOINTS_DIR)

    # 2. Normalise features
    n_samples, seq_len, n_feat = X.shape
    X_flat  = X.reshape(-1, n_feat)
    scaler  = StandardScaler()
    X_flat  = scaler.fit_transform(X_flat)
    X       = X_flat.reshape(n_samples, seq_len, n_feat)

    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    print(f"\nScaler saved → {SCALER_PATH}")

    # 3. Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train: {len(X_train)} sequences  |  Test: {len(X_test)} sequences")

    # 4. Build model
    model = build_lstm_model(SEQUENCE_LENGTH, NUM_FEATURES)
    model.summary()

    # 5. Train
    callbacks = [
        EarlyStopping(patience=10, restore_best_weights=True, verbose=1),
        ModelCheckpoint(MODEL_PATH, save_best_only=True, verbose=1),
    ]

    print("\nTraining...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=50,
        batch_size=16,
        callbacks=callbacks,
        verbose=1,
    )

    # 6. Evaluate
    print("\n" + "=" * 60)
    print("Evaluation on test set")
    print("=" * 60)
    y_pred = (model.predict(X_test) > 0.5).astype(int).flatten()

    print(classification_report(y_test, y_pred, target_names=["Normal", "Fall"]))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    print(f"\nModel saved → {MODEL_PATH}")
    print("=" * 60)
    print("Done! Next step: run fall_detection_camera.py to test live.")
