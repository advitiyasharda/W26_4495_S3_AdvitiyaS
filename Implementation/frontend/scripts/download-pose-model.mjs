#!/usr/bin/env node
/**
 * download-pose-model.mjs
 *
 * Downloads the MediaPipe pose-landmarker model required by the Flask
 * backend's fall-detection feature.
 *
 * Output: ../models/pose_landmarker.task (relative to Implementation/)
 *
 * Runs automatically via `npm install` (see package.json -> postinstall).
 * Safe to run multiple times: exits early if the file already exists.
 *
 * Skip by setting SKIP_POSE_MODEL_DOWNLOAD=1 in the environment.
 */

import { existsSync, mkdirSync, createWriteStream, unlinkSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import https from "node:https";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Implementation/frontend/scripts/ -> Implementation/models/
const MODEL_DIR = resolve(__dirname, "..", "..", "models");
const MODEL_PATH = resolve(MODEL_DIR, "pose_landmarker.task");
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task";
const MIN_SIZE_BYTES = 1_000_000; // ~9MB file; anything smaller is bogus

if (process.env.SKIP_POSE_MODEL_DOWNLOAD === "1") {
  console.log("[pose-model] SKIP_POSE_MODEL_DOWNLOAD=1 set — skipping download.");
  process.exit(0);
}

if (existsSync(MODEL_PATH) && statSync(MODEL_PATH).size >= MIN_SIZE_BYTES) {
  console.log(`[pose-model] Already present at ${MODEL_PATH} — skipping.`);
  process.exit(0);
}

mkdirSync(MODEL_DIR, { recursive: true });

console.log(`[pose-model] Downloading ${MODEL_URL}`);
console.log(`[pose-model] -> ${MODEL_PATH}`);

function download(url, dest, redirectsLeft = 5) {
  return new Promise((resolvePromise, rejectPromise) => {
    const request = https.get(url, (response) => {
      const status = response.statusCode ?? 0;

      if (status >= 300 && status < 400 && response.headers.location) {
        if (redirectsLeft === 0) {
          rejectPromise(new Error("Too many redirects"));
          return;
        }
        response.resume();
        download(response.headers.location, dest, redirectsLeft - 1)
          .then(resolvePromise)
          .catch(rejectPromise);
        return;
      }

      if (status !== 200) {
        rejectPromise(new Error(`HTTP ${status} from ${url}`));
        response.resume();
        return;
      }

      const file = createWriteStream(dest);
      response.pipe(file);
      file.on("finish", () => file.close(() => resolvePromise()));
      file.on("error", (err) => {
        try { unlinkSync(dest); } catch {}
        rejectPromise(err);
      });
    });

    request.on("error", rejectPromise);
    request.setTimeout(60_000, () => {
      request.destroy(new Error("Timed out after 60s"));
    });
  });
}

try {
  await download(MODEL_URL, MODEL_PATH);
  const size = statSync(MODEL_PATH).size;
  if (size < MIN_SIZE_BYTES) {
    throw new Error(`Downloaded file is only ${size} bytes — looks corrupt.`);
  }
  console.log(`[pose-model] Done. ${(size / 1024 / 1024).toFixed(1)} MB written.`);
} catch (err) {
  console.error("[pose-model] Download failed:", err.message);
  console.error("[pose-model] You can run it manually:");
  console.error(
    `  curl -L -o models/pose_landmarker.task ${MODEL_URL}`
  );
  // Non-fatal: don't block npm install if the user is offline.
  process.exit(0);
}
