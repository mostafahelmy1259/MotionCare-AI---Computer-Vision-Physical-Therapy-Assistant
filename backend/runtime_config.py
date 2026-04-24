from __future__ import annotations

import os
import tempfile
import urllib.request
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_MODEL_PATH = BACKEND_DIR / "models" / "pose_landmarker_full.task"
DEFAULT_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)


def load_env_file(path: str | Path | None = None) -> None:
    env_path = Path(path) if path else BACKEND_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_model_path(model_path: str | Path | None = None) -> Path:
    configured = model_path or os.getenv("POSE_MODEL_PATH")
    if configured is None or str(configured).strip() == "":
        return DEFAULT_MODEL_PATH

    path = Path(configured).expanduser()
    if path.is_absolute():
        return path

    cwd_candidate = (Path.cwd() / path).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    backend_candidate = (BACKEND_DIR / path).resolve()
    if backend_candidate.exists() or str(path).startswith("models"):
        return backend_candidate

    return (PROJECT_ROOT / path).resolve()


def ensure_pose_model(model_path: str | Path | None = None, *, download: bool | None = None) -> Path:
    path = resolve_model_path(model_path)
    if path.exists() and path.stat().st_size > 0:
        return path

    should_download = bool_env("AUTO_DOWNLOAD_POSE_MODEL", True) if download is None else download
    if not should_download:
        raise FileNotFoundError(_missing_model_message(path))

    url = os.getenv("POSE_MODEL_URL", DEFAULT_MODEL_URL)
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(delete=False, dir=path.parent, suffix=".task") as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        urllib.request.urlretrieve(url, tmp_path)
        if tmp_path.stat().st_size == 0:
            raise RuntimeError("Downloaded model file is empty.")
        tmp_path.replace(path)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(f"{_missing_model_message(path)} Automatic download failed: {exc}") from exc

    return path


def _missing_model_message(path: Path) -> str:
    return (
        f"Pose Landmarker model not found at {path}. Run "
        "`python setup_runtime.py` from the backend folder or set POSE_MODEL_PATH."
    )
