# Troubleshooting Guide

---

## Backend Issues

### Flask won't start

**Symptom:** `python main.py` errors immediately.

**Common causes:**

1. **Virtual environment not active**
   ```bash
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

2. **Missing packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Port 5001 already in use**
   ```bash
   # Find what is using port 5001
   lsof -i :5001          # macOS/Linux
   netstat -ano | find "5001"  # Windows
   
   # Kill the process or change FLASK_PORT
   export FLASK_PORT=5002
   # Also update next.config.ts destination to :5002
   ```

4. **MediaPipe / protobuf / TensorFlow version conflict**  
   This is pre-handled in `api/__init__.py` with a TF stub module. If you still see:
   ```
   AttributeError: module 'google.protobuf' has no attribute...
   ```
   Try:
   ```bash
   pip install protobuf==4.25.0
   ```

5. **Model file missing**  
   Flask continues without models and logs warnings. Check `server.log` for lines like:
   ```
   WARNING FallDetector could not be initialised
   WARNING No trained anomaly model found
   ```

---

### Face recognition not working / always returning "Unknown"

1. **No faces enrolled**
   ```bash
   curl http://localhost:5001/api/recognition/status
   # Check "registered_persons" > 0
   ```
   If 0, run `python scripts/register_faces.py` or use the Demo Center.

2. **Face samples not matching any DB user**  
   The `data/samples/` folder name must match `user_id` in the `users` table, or the normalised (lowercase, alphanumeric only) form of the user's `name`.
   ```bash
   # Check what users exist in DB
   sqlite3 data/doorface.db "SELECT user_id, name FROM users;"
   
   # List sample folders
   ls data/samples/
   ```

3. **Wrong engine mode**  
   Install `face_recognition` for better accuracy:
   ```bash
   pip install face_recognition
   # Restart Flask; check engine_mode in /api/recognition/status
   ```

4. **Distance threshold too strict**  
   Lower `FACE_CONFIDENCE_THRESHOLD` in `config.py` or run:
   ```bash
   python scripts/calibrate_recognition.py
   ```

5. **Low lighting or poor angle**  
   Photos captured in the same conditions as the live scene work best. Recapture:
   ```bash
   python scripts/capture_faces.py --person {name} --photos 40
   ```

---

### Fall detection camera script crashes

**Symptom:** `fall_detection_camera.py` exits immediately or segfaults.

1. **MediaPipe pose model not found**
   ```
   RuntimeError: Unable to open file: models/pose_landmarker.task
   ```
   The model downloads automatically on `npm install`. Manual download:
   ```bash
   cd Implementation/frontend
   npm run postinstall
   ```
   Or directly:
   ```bash
   curl -L -o Implementation/models/pose_landmarker.task \
     "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
   ```

2. **Camera not accessible (macOS)**  
   Grant camera permission to Terminal in System Preferences → Privacy → Camera. The script sets `OPENCV_VIDEOIO_PRIORITY_AVFOUNDATION=1000` automatically.

3. **Wrong camera index**  
   Try changing the camera index in `fall_detection_camera.py`:
   ```python
   cap = cv2.VideoCapture(1)   # try 0, 1, 2
   ```

---

### Object detection not finding anything

1. **YOLO model missing**
   ```
   ls Implementation/yolo26l.pt   # should exist
   ```
   The model must be in the directory from which the script is run.

2. **Confidence threshold too high**  
   Lower `OBJECT_DETECTION_CONFIDENCE` in `config.py` or set env var.

3. **Preprocessing making things worse**  
   Try disabling CLAHE: `export OBJECT_ENABLE_PREPROCESSING=0`

---

### `POST /api/log-access` does nothing

This is a **known stub** — the endpoint exists but does not write to the database. It only logs to the console. If you need it to persist, implement the `db.log_access()` call in `api/routes.py` in the `log_access()` function (the TODO comment is there).

---

## Frontend Issues

### Dashboard shows no data (all charts empty)

1. **Demo mode is OFF and backend is not running**  
   Either start the backend (`python main.py`) or turn on the demo toggle (purple switch in the sidebar).

2. **Demo mode is ON but you're not seeing demo data**  
   Check `localStorage` in browser DevTools (Application → Local Storage → `facedoor_demo_mode`). If it's `"false"`, click the toggle to switch it ON.

3. **Next.js can't reach the API**  
   Open browser DevTools → Network tab. Look for failed `/api/*` requests. If they return 502 or fail, Flask is not running or is on a different port.  
   Check `next.config.ts` — the proxy destination must match Flask's actual port.

---

### "API fetch failed" in browser console

This means the `/api/...` request failed. Most common causes:
- Flask is not running
- Flask is running on a different port than `next.config.ts` expects (should be 5001)
- CORS error — this should not occur since the frontend uses the Next.js proxy, but if you're calling Flask directly from the browser, add the origin to CORS in `api/__init__.py`

---

### Demo toggle appears in wrong position / overflows

If the toggle appears outside the sidebar or overlaps text, check that:
- `Sidebar.tsx` has `overflow-hidden` on the toggle `<button>`
- The thumb `<span>` uses `left-0.5` and `translate-x-0` / `translate-x-4`

---

### Frontend build fails (`npm run build`)

1. **ESLint errors**
   ```bash
   npm run lint
   ```
   Fix reported issues, or temporarily add to `.eslintrc`:
   ```json
   { "rules": { "the-rule": "off" } }
   ```

2. **TypeScript errors**
   ```bash
   npx tsc --noEmit
   ```

3. **`node_modules` corrupted**
   ```bash
   rm -rf node_modules .next
   npm install
   ```

---

### MediaPipe pose model download fails during `npm install`

The postinstall script (`scripts/download-pose-model.mjs`) downloads from Google Storage. If behind a corporate proxy or with no internet:

```bash
# Skip the download
SKIP_POSE_MODEL_DOWNLOAD=1 npm install

# Manually copy the model later
cp /path/to/pose_landmarker_lite.task public/models/pose_landmarker.task
```

---

## Database Issues

### Database locked errors

SQLite single-writer limitation. Because Flask runs `threaded=False`, this should not occur under normal single-user operation. If you see:

```
sqlite3.OperationalError: database is locked
```

Check if another process (e.g. a script) has the DB open, or if you started Flask with `threaded=True` accidentally.

---

### Too many threats in the database

After repeated testing, the `threats` table can accumulate thousands of rows. To clear:

```bash
# Clear only threats (keep users and logs)
sqlite3 Implementation/data/doorface.db "DELETE FROM threats;"

# Or clear everything
python Implementation/scripts/clear_database.py
```

---

### Wrong timestamps on events

Timestamps are stored as UTC in the database. The frontend adds `Z` suffix where missing (in `routes.py` and `fall_detection_routes.py`). If timestamps appear to be off by your timezone offset, check that:
- Timestamps in the DB have the `Z` suffix (or `+HH:MM` offset)
- The frontend's `new Date(timestamp)` call is receiving a valid ISO string

---

## Demo Center Issues

### Camera script starts but nothing happens

1. Backend logs are suppressed for demo subprocesses (`stdout=DEVNULL`). To debug, run the script manually in a terminal instead.
2. Check if another camera tool is running — only one can run at a time; starting a new one stops the previous.
3. Check `server.log` for subprocess errors.

### "Face-register" tool starts but doesn't complete registration

The capture runs in a separate process. Registration happens at the end of capture (after N photos). If the process was stopped early, run manually:

```bash
python scripts/capture_faces.py \
  --person {name} \
  --photos 40 \
  --register-now \
  --person-id {id} \
  --display-name "{Name}" \
  --role resident \
  --reload-api-url http://localhost:5001
```

---

## Performance Issues

### Recognition is slow (> 1 second per frame)

1. Install `face_recognition` (dlib) — it is faster than OpenCV for feature extraction
2. Reduce frame size before sending to the API (720p is sufficient)
3. On Raspberry Pi, expect ~2–3 seconds; consider running recognition every 3rd frame

### Object detection is slow on CPU

Lower the image size:

```bash
export OBJECT_IMGSZ=320
python main.py
```

Or use a smaller YOLO model: replace `yolo26l.pt` with `yolo26m.pt` or `yolov8n.pt` (both are in `Implementation/`).

### High CPU usage at idle

The Flask server is idle without camera input. If CPU is high, check if a demo script is stuck. Use the Demo Center to stop it, or:

```bash
# Find and kill stuck processes
ps aux | grep python
kill {pid}
```
