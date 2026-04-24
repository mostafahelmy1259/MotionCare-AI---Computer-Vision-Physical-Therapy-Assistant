# AI Physical Therapy Rehabilitation Coach

A web-based AI rehabilitation assistant that uses computer vision to track patient movement, calculate joint angles, count repetitions, detect form mistakes, and generate therapist-style session reports.

This project uses a **React frontend** and a **Python FastAPI backend**.  
The backend runs OpenCV + MediaPipe Pose Landmarker, while the frontend displays the live rehabilitation dashboard.

---

## Project Structure

```text
Physical Therapy Project/
│
├── backend/
│   ├── main.py                 # FastAPI API + WebSocket server
│   ├── pose_tracker.py          # OpenCV + MediaPipe tracking
│   ├── exercises.py             # Exercise logic, stages, reps, feedback
│   ├── report_generator.py      # Final session report generation
│   ├── runtime_config.py        # Environment/model path configuration
│   ├── setup_runtime.py         # Downloads/validates MediaPipe model
│   ├── requirements.txt         # Backend Python dependencies
│   ├── .env.example             # Backend environment example
│   └── models/                  # MediaPipe model file location
│
├── frontend/
│   ├── package.json             # Frontend dependencies and scripts
│   ├── vite.config.js           # Vite dev server/proxy config
│   ├── .env.example             # Frontend environment example
│   └── src/
│       ├── App.jsx              # Main React dashboard
│       ├── components/          # UI components
│       └── styles.css           # Styling
│
├── README.md
└── .gitignore
```

---

## Tech Stack

### Backend

- Python 3.13
- FastAPI
- Uvicorn
- OpenCV
- MediaPipe Tasks API / Pose Landmarker
- WebSocket for real-time metrics

### Frontend

- React
- Vite
- JavaScript
- CSS

---

## Important Notes

This project does **not** use:

- Unity
- VR SDK
- raw TCP sockets
- `mp.solutions`

The project uses the newer **MediaPipe Tasks API**, which is compatible with your Python 3.13 setup.

---

# How to Run the Project

The project must be started in two terminals:

1. One terminal for the **backend**
2. One terminal for the **frontend**

---

## 1. Open the Project Folder

Open PowerShell and go to your project folder:

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project"
```

---

# Backend Setup

## 2. Go to the Backend Folder

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\backend"
```

---

## 3. Create a Virtual Environment

Use your real Python 3.13 executable directly:

```powershell
& "C:\Users\m8325\AppData\Local\Programs\Python\Python313\python.exe" -m venv .venv
```

---

## 4. Activate the Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, your terminal should show something like:

```text
(.venv) PS C:\Users\m8325\Downloads\Physical Therapy Project\backend>
```

---

## 5. Upgrade Pip

```powershell
python -m pip install --upgrade pip
```

---

## 6. Install Backend Dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## 7. Download / Prepare the MediaPipe Model

```powershell
python setup_runtime.py
```

The backend expects the MediaPipe pose model here:

```text
backend\models\pose_landmarker_full.task
```

If the model already exists, the script should not download it again.

---

## 8. Start the Backend Server

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If everything is correct, you should see:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

Keep this terminal open.

---

# Frontend Setup

Open a **new PowerShell terminal**.

---

## 9. Go to the Frontend Folder

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\frontend"
```

---

## 10. Install Frontend Dependencies

```powershell
npm install
```

---

## 11. Start the Frontend

```powershell
npm run dev
```

If everything is correct, Vite should show something like:

```text
Local: http://localhost:5173/
```

Open this URL in your browser:

```text
http://localhost:5173/
```

---

# How to Use the App

1. Start the backend server.
2. Start the frontend server.
3. Open the frontend URL in your browser.
4. Select an exercise.
5. Click **Start Session**.
6. Allow camera permission if the browser asks.
7. Perform the exercise in front of the webcam.
8. Watch the live metrics:
   - current angle
   - rep count
   - correct reps
   - wrong reps
   - feedback message
9. Click **Finish Session**.
10. View the final rehabilitation report.

---

# Expected Backend Logs

When the frontend starts and connects, the backend should show logs like:

```text
GET /api/exercises HTTP/1.1" 200 OK
POST /api/session/start HTTP/1.1" 200 OK
WebSocket /ws/track/<session_id> [accepted]
connection open
Created TensorFlow Lite XNNPACK delegate for CPU.
```

When the session finishes:

```text
POST /api/session/<session_id>/finish HTTP/1.1" 200 OK
connection closed
```

These are good signs.

---

# Normal MediaPipe Warnings

You may see warnings like:

```text
Feedback manager requires a model with a single signature inference.
```

or:

```text
Using NORM_RECT without IMAGE_DIMENSIONS is only supported for the square ROI.
```

These warnings are normal MediaPipe/TensorFlow Lite messages.  
If the webcam opens and tracking works, you can ignore them.

---

# Troubleshooting

## Problem: `py` launcher gives Access Denied

If this command fails:

```powershell
py --version
```

Use the full Python path instead:

```powershell
& "C:\Users\m8325\AppData\Local\Programs\Python\Python313\python.exe" --version
```

For this project, prefer using the virtual environment after setup:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
```

---

## Problem: PowerShell blocks activation

If this fails:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then try again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Problem: Webcam does not open

Possible reasons:

1. Another app is using the webcam.
2. Windows privacy settings block camera access.
3. Browser camera permission was denied.
4. The backend cannot access the default camera.

Try:

- Close Zoom, Teams, OBS, Camera app, or other webcam apps.
- Check Windows camera privacy settings.
- Refresh the browser and allow camera access.
- Restart the backend.

---

## Problem: Port 8000 already in use

If backend fails because port 8000 is already used, stop the old backend with `CTRL + C`.

Or run on another port:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

If you change the backend port, also update the frontend API/WebSocket configuration.

---

## Problem: `npm install` fails

Try cleaning npm cache inside the frontend folder:

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\frontend"
npm cache clean --force
npm install
```

If permissions are the issue, try:

```powershell
npm config set cache ".npm-cache" --location=project
npm install
```

---

## Problem: Frontend does not connect to backend

Make sure the backend is running first:

```text
http://127.0.0.1:8000
```

Then restart the frontend:

```powershell
npm run dev
```

Also check that the frontend is using the correct backend URL, usually:

```text
http://127.0.0.1:8000
```

and WebSocket URL:

```text
ws://127.0.0.1:8000
```

---

## Problem: Angle does not update

Check:

1. Your body/arm is visible in the camera.
2. Lighting is good.
3. The selected exercise matches the movement.
4. The correct body side is visible.
5. The backend WebSocket is connected.

For seated testing, use upper-body exercises first, such as:

```text
Seated Bicep Curl
Seated Shoulder Raise
```

These are easier to track than knee exercises if you are sitting close to the camera.

---

# Recommended Demo Flow

For a clean project demo:

1. Open backend terminal.
2. Run the backend.
3. Open frontend terminal.
4. Run the frontend.
5. Open the browser dashboard.
6. Select **Seated Bicep Curl**.
7. Click **Start Session**.
8. Perform 3 to 5 reps.
9. Show:
   - live angle
   - rep counter
   - feedback box
10. Click **Finish Session**.
11. Show the final report.

---

# Project Description

This project is an AI-powered physical therapy rehabilitation coach.  
It uses computer vision to track the patient's body movement through a webcam, calculates rehabilitation-related joint angles, counts exercise repetitions, gives real-time form feedback, and generates a therapist-style report at the end of each session.

---

# Current Project Status

Working features:

- React frontend dashboard
- FastAPI backend
- WebSocket real-time tracking
- OpenCV webcam capture
- MediaPipe Pose Landmarker
- Exercise selection
- Angle calculation
- Repetition counting
- Real-time feedback
- Session finish flow
- Final report generation

---

# Limitations

This is an academic prototype, not a certified medical device.

Current limitations:

- Accuracy depends on webcam position and lighting.
- Tracking may fail if body landmarks are hidden.
- It is not clinically validated.
- It does not replace a real physical therapist.
- No user accounts or cloud database are included by default.

---

# Future Work

Possible improvements:

- Add AI-generated therapist feedback.
- Add user accounts and patient history.
- Store session reports in a database.
- Add more rehabilitation exercises.
- Add progress charts.
- Add PDF export for reports.
- Add voice feedback.
- Add therapist/admin dashboard.
- Validate angle accuracy against real clinical measurements.

---

# Quick Command Summary

## Backend

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\backend"
& "C:\Users\m8325\AppData\Local\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python setup_runtime.py
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```powershell
cd "C:\Users\m8325\Downloads\Physical Therapy Project\frontend"
npm install
npm run dev
```

Open:

```text
http://localhost:5173/
```
