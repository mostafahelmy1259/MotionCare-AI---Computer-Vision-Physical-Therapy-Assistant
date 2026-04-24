from __future__ import annotations

import base64
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .runtime_config import ensure_pose_model, resolve_model_path
except ImportError:
    from runtime_config import ensure_pose_model, resolve_model_path


POSE_LANDMARKS = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
}

UPPER_BODY_CONNECTIONS = (
    ("left_shoulder", "right_shoulder"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("right_shoulder", "right_hip"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("left_shoulder", "left_hip"),
    ("left_hip", "right_hip"),
)

REQUIRED_RIGHT_SIDE = ("right_shoulder", "right_elbow", "right_wrist", "right_hip")


@dataclass
class PoseFrame:
    frame: str
    angles: dict[str, float]
    visibility_ok: bool
    visibility_issue: str | None
    timestamp_ms: int


def calculate_angle(a: Any, b: Any, c: Any) -> float:
    ab_x = a.x - b.x
    ab_y = a.y - b.y
    cb_x = c.x - b.x
    cb_y = c.y - b.y
    ab_norm = math.hypot(ab_x, ab_y)
    cb_norm = math.hypot(cb_x, cb_y)
    if ab_norm == 0 or cb_norm == 0:
        return 0.0

    cosine = (ab_x * cb_x + ab_y * cb_y) / (ab_norm * cb_norm)
    angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    return angle


class PoseTracker:
    def __init__(
        self,
        camera_index: int | None = None,
        model_path: str | Path | None = None,
        width: int = 960,
        height: int = 540,
        jpeg_quality: int = 80,
        visibility_threshold: float = 0.55,
    ) -> None:
        self.camera_index = camera_index if camera_index is not None else int(os.getenv("CAMERA_INDEX", "0"))
        self.model_path = resolve_model_path(model_path)
        self.width = width
        self.height = height
        self.jpeg_quality = jpeg_quality
        self.visibility_threshold = visibility_threshold
        self.capture: Any | None = None
        self.landmarker: Any | None = None
        self._cv2: Any | None = None
        self._mp: Any | None = None
        self._vision: Any | None = None

    def __enter__(self) -> "PoseTracker":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def start(self) -> None:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        self.model_path = ensure_pose_model(self.model_path)
        self._cv2 = cv2
        self._mp = mp
        self._vision = vision

        self.capture = self._cv2.VideoCapture(self.camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open webcam at index {self.camera_index}.")

        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def read(self) -> PoseFrame:
        if self.capture is None or self.landmarker is None or self._cv2 is None or self._mp is None:
            raise RuntimeError("PoseTracker.start() must be called before read().")

        ok, frame = self.capture.read()
        if not ok or frame is None:
            raise RuntimeError("Could not read a frame from the webcam.")

        timestamp_ms = int(time.monotonic() * 1000)
        rgb_frame = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        angles: dict[str, float] = {}
        visibility_ok = False
        visibility_issue = "No person detected. Sit centered in the camera view."

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            visibility_ok, visibility_issue = self._check_visibility(landmarks)
            if visibility_ok:
                angles = self._calculate_angles(landmarks)
            frame = self._draw_overlay(frame, landmarks, visibility_ok)
        else:
            frame = self._draw_status(frame, visibility_issue, ok=False)

        frame_data = self._encode_frame(frame)
        return PoseFrame(
            frame=frame_data,
            angles=angles,
            visibility_ok=visibility_ok,
            visibility_issue=visibility_issue,
            timestamp_ms=timestamp_ms,
        )

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        if self.landmarker is not None:
            self.landmarker.close()
            self.landmarker = None

    def _calculate_angles(self, landmarks: list[Any]) -> dict[str, float]:
        right_shoulder = landmarks[POSE_LANDMARKS["right_shoulder"]]
        right_elbow = landmarks[POSE_LANDMARKS["right_elbow"]]
        right_wrist = landmarks[POSE_LANDMARKS["right_wrist"]]
        right_hip = landmarks[POSE_LANDMARKS["right_hip"]]

        return {
            "right_elbow": calculate_angle(right_shoulder, right_elbow, right_wrist),
            "right_shoulder": calculate_angle(right_hip, right_shoulder, right_elbow),
        }

    def _check_visibility(self, landmarks: list[Any]) -> tuple[bool, str | None]:
        low_visibility: list[str] = []

        for name in REQUIRED_RIGHT_SIDE:
            landmark = landmarks[POSE_LANDMARKS[name]]
            visibility = float(getattr(landmark, "visibility", 1.0) or 0.0)
            presence = float(getattr(landmark, "presence", 1.0) or 0.0)
            inside_frame = 0.0 <= landmark.x <= 1.0 and 0.0 <= landmark.y <= 1.0
            if visibility < self.visibility_threshold or presence < self.visibility_threshold or not inside_frame:
                low_visibility.append(name.replace("_", " "))

        if low_visibility:
            joints = ", ".join(low_visibility)
            return False, f"Improve camera visibility for: {joints}."

        return True, None

    def _draw_overlay(self, frame: Any, landmarks: list[Any], visibility_ok: bool) -> Any:
        if self._cv2 is None:
            return frame

        height, width = frame.shape[:2]
        line_color = (46, 204, 113) if visibility_ok else (59, 130, 246)
        point_color = (255, 255, 255)

        for start_name, end_name in UPPER_BODY_CONNECTIONS:
            start = landmarks[POSE_LANDMARKS[start_name]]
            end = landmarks[POSE_LANDMARKS[end_name]]
            start_xy = (int(start.x * width), int(start.y * height))
            end_xy = (int(end.x * width), int(end.y * height))
            self._cv2.line(frame, start_xy, end_xy, line_color, 3)

        for name in POSE_LANDMARKS:
            landmark = landmarks[POSE_LANDMARKS[name]]
            center = (int(landmark.x * width), int(landmark.y * height))
            self._cv2.circle(frame, center, 5, point_color, -1)
            self._cv2.circle(frame, center, 7, line_color, 2)

        status = "Tracking ready" if visibility_ok else "Adjust camera"
        return self._draw_status(frame, status, ok=visibility_ok)

    def _draw_status(self, frame: Any, text: str, ok: bool) -> Any:
        if self._cv2 is None:
            return frame

        color = (46, 204, 113) if ok else (52, 73, 94)
        self._cv2.rectangle(frame, (18, 18), (390, 62), (16, 24, 39), -1)
        self._cv2.putText(
            frame,
            text[:42],
            (32, 48),
            self._cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            color,
            2,
            self._cv2.LINE_AA,
        )
        return frame

    def _encode_frame(self, frame: Any) -> str:
        if self._cv2 is None:
            raise RuntimeError("OpenCV is not initialized.")

        encode_params = [int(self._cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        ok, buffer = self._cv2.imencode(".jpg", frame, encode_params)
        if not ok:
            raise RuntimeError("Could not encode webcam frame.")
        encoded = base64.b64encode(buffer).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
