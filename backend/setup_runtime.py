from __future__ import annotations

from runtime_config import DEFAULT_MODEL_URL, ensure_pose_model, load_env_file


def main() -> None:
    load_env_file()
    model_path = ensure_pose_model(download=True)
    print(f"Pose model ready: {model_path}")
    print(f"Model source: {DEFAULT_MODEL_URL}")


if __name__ == "__main__":
    main()
