from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .exercises import EXERCISES, ExerciseCounter, list_exercises
    from .pose_tracker import PoseTracker
    from .report_generator import generate_report
    from .runtime_config import load_env_file, resolve_model_path
except ImportError:
    from exercises import EXERCISES, ExerciseCounter, list_exercises
    from pose_tracker import PoseTracker
    from report_generator import generate_report
    from runtime_config import load_env_file, resolve_model_path


load_env_file()


class StartSessionRequest(BaseModel):
    exercise: str


@dataclass
class RehabSession:
    session_id: str
    exercise: str
    counter: ExerciseCounter
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True
    samples: list[dict[str, Any]] = field(default_factory=list)
    latest_payload: dict[str, Any] | None = None

    def record(self, payload: dict[str, Any]) -> None:
        self.latest_payload = payload
        sample = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "angle": payload.get("angle"),
            "stage": payload.get("stage"),
            "reps": payload.get("reps"),
            "correct_reps": payload.get("correct_reps"),
            "wrong_reps": payload.get("wrong_reps"),
            "visibility_ok": payload.get("visibility_ok"),
            "feedback": payload.get("feedback"),
            "mistake": payload.get("mistake"),
            "rom": payload.get("rom"),
            "rep_event": payload.get("rep_event"),
        }
        self.samples.append(sample)

    @property
    def duration_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()


app = FastAPI(title="AI Rehabilitation Coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, RehabSession] = {}
CAMERA_STATE_LOCK = asyncio.Lock()
CAMERA_IN_USE = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/runtime")
def runtime_status() -> dict[str, Any]:
    model_path = resolve_model_path()
    return {
        "status": "ok",
        "model_path": str(model_path),
        "model_exists": model_path.exists(),
        "camera_in_use": CAMERA_IN_USE,
    }


@app.get("/api/exercises")
def get_exercises() -> list[dict[str, str]]:
    return list_exercises()


@app.post("/api/session/start")
def start_session(request: StartSessionRequest) -> dict[str, Any]:
    if request.exercise not in EXERCISES:
        raise HTTPException(status_code=400, detail=f"Unsupported exercise '{request.exercise}'.")

    session_id = str(uuid.uuid4())
    session = RehabSession(
        session_id=session_id,
        exercise=request.exercise,
        counter=ExerciseCounter(request.exercise),
    )
    SESSIONS[session_id] = session

    return {
        "session_id": session_id,
        "exercise": request.exercise,
        "exercise_label": EXERCISES[request.exercise].label,
        "started_at": session.started_at.isoformat(),
    }


@app.post("/api/session/{session_id}/finish")
def finish_session(session_id: str) -> dict[str, Any]:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    session.active = False
    return generate_report(session)


@app.get("/api/session/{session_id}/latest")
def latest_session_payload(session_id: str) -> dict[str, Any]:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session.latest_payload or {"session_id": session_id, "message": "No tracking data yet."}


@app.websocket("/ws/track/{session_id}")
async def track_session(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()

    session = SESSIONS.get(session_id)
    if session is None:
        await websocket.send_json({"type": "error", "error": "Session not found."})
        await websocket.close(code=1008)
        return

    if not await _claim_camera():
        await websocket.send_json({"type": "error", "error": "The webcam is already in use by another session."})
        await websocket.close(code=1013)
        return

    tracker: PoseTracker | None = None
    try:
        tracker = PoseTracker()
        await websocket.send_json(
            {
                "type": "status",
                "session_id": session_id,
                "message": "Opening camera and loading pose model.",
                "exercise": session.exercise,
                "exercise_label": EXERCISES[session.exercise].label,
            }
        )
        await asyncio.to_thread(tracker.start)
        await websocket.send_json(
            {
                "type": "status",
                "session_id": session_id,
                "message": "Tracking started.",
                "exercise": session.exercise,
                "exercise_label": EXERCISES[session.exercise].label,
            }
        )

        while session.active:
            pose_frame = await asyncio.to_thread(tracker.read)
            metrics = session.counter.update(
                pose_frame.angles,
                visibility_ok=pose_frame.visibility_ok,
                visibility_issue=pose_frame.visibility_issue,
            )
            payload = {
                **metrics,
                "type": "metrics",
                "session_id": session_id,
                "timestamp_ms": pose_frame.timestamp_ms,
                "frame": pose_frame.frame,
            }
            session.record(payload)
            await websocket.send_json(payload)
            await asyncio.sleep(0.03)

        await websocket.send_json({"type": "status", "session_id": session_id, "message": "Session finished."})

    except WebSocketDisconnect:
        session.active = False
    except Exception as exc:
        session.active = False
        await _send_error(websocket, str(exc))
    finally:
        if tracker is not None:
            await asyncio.to_thread(tracker.close)
        await _release_camera()


async def _send_error(websocket: WebSocket, message: str) -> None:
    try:
        await websocket.send_json({"type": "error", "error": message})
        await websocket.close(code=1011)
    except RuntimeError:
        pass


async def _claim_camera() -> bool:
    global CAMERA_IN_USE
    async with CAMERA_STATE_LOCK:
        if CAMERA_IN_USE:
            return False
        CAMERA_IN_USE = True
        return True


async def _release_camera() -> None:
    global CAMERA_IN_USE
    async with CAMERA_STATE_LOCK:
        CAMERA_IN_USE = False
