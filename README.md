# MotionCare-AI---Computer-Vision-Physical-Therapy-Assistant
MotionCare AI is a computer vision–based rehabilitation coach that helps patients perform physical therapy exercises correctly. It uses real-time pose tracking to calculate joint angles, count repetitions, detect form mistakes, provide instant feedback, and generate session reports for progress review.

Web-based rehabilitation dashboard with a React + Vite frontend and a Python FastAPI backend. The backend opens the webcam only when a browser WebSocket tracking session starts, runs MediaPipe Tasks `PoseLandmarker`, counts seated upper-body repetitions, and streams live camera frames plus exercise metrics to the dashboard.

## Features

- FastAPI backend with REST session endpoints and WebSocket live tracking.
- OpenCV webcam capture.
- MediaPipe Tasks API `PoseLandmarker`; no `mp.solutions`.
- Base64 JPEG frame stream over WebSocket.
- Seated Bicep Curl and Seated Shoulder Raise.
- Right elbow and right shoulder angle calculation.
- Rep stage logic, visibility detection, correct/wrong rep counts, ROM metrics, and final clinical report.
- React + Vite dashboard with camera, metrics, feedback, and report panels.

## Project Structure

```text
backend/
  main.py
  pose_tracker.py
  exercises.py
  report_generator.py
  runtime_config.py
  setup_runtime.py
  requirements.txt
  models/
frontend/
  index.html
  package.json
  vite.config.js
  src/
```

## Windows PowerShell Setup

Run these commands from a normal Windows PowerShell terminal.

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project"
```

Install Python 3.13 and Node.js if needed:

```powershell
winget install --id Python.Python.3.13 -e
winget install --id OpenJS.NodeJS.LTS -e
```

Close and reopen PowerShell, then verify:

```powershell
py -3.13 --version
node --version
npm.cmd --version
```

If `py -3.13 --version` returns `Access is denied` from a `WindowsApps` path, install Python from python.org or disable the Microsoft Store Python app execution aliases in Windows Settings, then reopen PowerShell.

## Backend Setup

This machine has a working Python at:

```text
C:\Users\m8325\AppData\Local\Programs\Python\Python313\python.exe
```

Use that direct path if the `py` launcher points to the blocked WindowsApps interpreter.

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\backend"

$Python313 = "C:\Users\m8325\AppData\Local\Programs\Python\Python313\python.exe"
& $Python313 -m venv .venv

New-Item -ItemType Directory -Force -Path .tmp, .pip-cache | Out-Null
$env:TEMP = (Resolve-Path .tmp).Path
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = (Resolve-Path .pip-cache).Path

.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe setup_runtime.py
```

If `venv` creates `.venv` but pip is missing because `ensurepip` cannot write to `%TEMP%`, bootstrap pip from Python's bundled wheel:

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\backend"

$BundledPip = "C:\Users\m8325\AppData\Local\Programs\Python\Python313\Lib\ensurepip\_bundled\pip-25.1.1-py3-none-any.whl"
tar -xf $BundledPip -C ".\.venv\Lib\site-packages"
.\.venv\Scripts\python.exe -m pip --version
```

`setup_runtime.py` downloads the default MediaPipe model to:

```text
backend\models\pose_landmarker_full.task
```

If automatic download is blocked, download this file in a browser and save it as `backend\models\pose_landmarker_full.task`:

```text
https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```

To use a different camera or model, edit `backend\.env`:

```powershell
CAMERA_INDEX=0
POSE_MODEL_PATH=models/pose_landmarker_full.task
AUTO_DOWNLOAD_POSE_MODEL=true
```

Start the backend:

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\backend"
New-Item -ItemType Directory -Force -Path .tmp | Out-Null
$env:TEMP = (Resolve-Path .tmp).Path
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Check the API in another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/runtime
```

Backend import check after dependencies are installed:

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\backend"
.\.venv\Scripts\python.exe -c "import fastapi, uvicorn, cv2, mediapipe, numpy, pydantic; import main; print('backend imports ok')"
```

## Frontend Setup

In a second PowerShell window:

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\frontend"
New-Item -ItemType Directory -Force -Path .npm-cache | Out-Null
npm.cmd ping
npm.cmd install
npm.cmd run dev
```

Open:

```text
http://127.0.0.1:5173
```

The default Vite dev server proxies `/api` and `/ws` to `http://127.0.0.1:8000`, so a frontend `.env` file is optional for local development. If you serve the frontend separately, create `frontend\.env`:

```powershell
Copy-Item .env.example .env
```

## Running A Session

1. Start the backend.
2. Start the frontend.
3. Open `http://127.0.0.1:5173`.
4. Select `Seated Bicep Curl` or `Seated Shoulder Raise`.
5. Select `Start Session`.
6. Allow webcam access if Windows prompts for it.
7. Keep the right shoulder, elbow, wrist, and hip visible.
8. Select `Finish Session` to generate the report.

## API Summary

- `GET /health` returns backend status.
- `GET /api/runtime` returns model path and camera lock status.
- `GET /api/exercises` returns exercise metadata.
- `POST /api/session/start` creates a session.
- `WS /ws/track/{session_id}` streams frames and metrics.
- `POST /api/session/{session_id}/finish` ends tracking and returns the report.

Example WebSocket metrics payload:

```json
{
  "type": "metrics",
  "exercise": "bicep_curl",
  "angle": 92.4,
  "angle_name": "right_elbow",
  "stage": "up",
  "reps": 4,
  "correct_reps": 3,
  "wrong_reps": 1,
  "feedback": "Good rep",
  "visibility_ok": true
}
```

## Troubleshooting

- Backend starts but tracking fails: run `.\.venv\Scripts\python.exe setup_runtime.py` and confirm `backend\models\pose_landmarker_full.task` exists.
- Webcam does not open: close Teams/Zoom/Camera apps, then set `CAMERA_INDEX=1` in `backend\.env` if your webcam is not device `0`.
- PowerShell blocks npm: use `npm.cmd install` and `npm.cmd run dev`.
- `pip install` fails with `WinError 10051`: the machine cannot reach PyPI from the current network. Reconnect to the network or retry from a terminal with internet access.
- `npm install` fails with `EACCES` or cannot reach `registry.npmjs.org`: create `..\.npm-cache` as shown above and verify internet access with `npm.cmd ping`.
- Browser cannot connect: confirm backend is running at `http://127.0.0.1:8000` and Vite at `http://127.0.0.1:5173`.
- Only one live tracking session can own the webcam at a time.

