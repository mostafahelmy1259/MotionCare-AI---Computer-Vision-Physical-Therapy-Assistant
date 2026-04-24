# MediaPipe Model

The runtime setup script downloads the MediaPipe Pose Landmarker Tasks model into this directory:

```text
pose_landmarker_full.task
```

From `backend`, run:

```powershell
.\.venv\Scripts\python.exe setup_runtime.py
```

The backend also supports a custom model path through the `POSE_MODEL_PATH` environment variable.
