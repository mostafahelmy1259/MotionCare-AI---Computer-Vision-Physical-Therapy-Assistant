from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExerciseConfig:
    key: str
    label: str
    angle_name: str
    down_threshold: float
    up_threshold: float
    min_rom: float
    target_min_angle: float
    target_max_angle: float
    instructions: str


EXERCISES: dict[str, ExerciseConfig] = {
    "bicep_curl": ExerciseConfig(
        key="bicep_curl",
        label="Seated Bicep Curl",
        angle_name="right_elbow",
        down_threshold=150.0,
        up_threshold=70.0,
        min_rom=75.0,
        target_min_angle=70.0,
        target_max_angle=145.0,
        instructions="Sit upright, keep the right elbow close to the body, curl up, then lower with control.",
    ),
    "shoulder_raise": ExerciseConfig(
        key="shoulder_raise",
        label="Seated Shoulder Raise",
        angle_name="right_shoulder",
        down_threshold=35.0,
        up_threshold=85.0,
        min_rom=50.0,
        target_min_angle=40.0,
        target_max_angle=85.0,
        instructions="Sit tall, raise the right arm toward shoulder height, then lower smoothly.",
    ),
}


@dataclass
class RepCandidate:
    min_angle: float | None = None
    max_angle: float | None = None
    had_visibility_issue: bool = False

    def update(self, angle: float, visibility_ok: bool) -> None:
        self.min_angle = angle if self.min_angle is None else min(self.min_angle, angle)
        self.max_angle = angle if self.max_angle is None else max(self.max_angle, angle)
        if not visibility_ok:
            self.had_visibility_issue = True

    @property
    def rom(self) -> float:
        if self.min_angle is None or self.max_angle is None:
            return 0.0
        return max(0.0, self.max_angle - self.min_angle)


@dataclass
class ExerciseCounter:
    exercise_key: str
    stage: str = "not_ready"
    reps: int = 0
    correct_reps: int = 0
    wrong_reps: int = 0
    completed_roms: list[float] = field(default_factory=list)
    mistakes: list[str] = field(default_factory=list)
    candidate: RepCandidate = field(default_factory=RepCandidate)

    def __post_init__(self) -> None:
        if self.exercise_key not in EXERCISES:
            available = ", ".join(sorted(EXERCISES))
            raise ValueError(f"Unsupported exercise '{self.exercise_key}'. Available: {available}")
        self.config = EXERCISES[self.exercise_key]

    def update(self, angles: dict[str, float], visibility_ok: bool, visibility_issue: str | None = None) -> dict[str, Any]:
        angle = angles.get(self.config.angle_name)

        if angle is None:
            if not visibility_ok and self.stage in {"down", "up", "moving"}:
                self.candidate.had_visibility_issue = True
            feedback = visibility_issue or "Move fully into the camera frame."
            return self._payload(None, feedback, visibility_ok=False, mistake="Tracking unavailable")

        self.candidate.update(angle, visibility_ok)

        if not visibility_ok:
            feedback = visibility_issue or "Improve visibility before continuing."
            return self._payload(angle, feedback, visibility_ok=False, mistake="Visibility problem")

        if self.exercise_key == "bicep_curl":
            feedback, mistake, rep_event = self._update_bicep_curl(angle)
        else:
            feedback, mistake, rep_event = self._update_shoulder_raise(angle)

        return self._payload(
            angle,
            feedback,
            visibility_ok=True,
            mistake=mistake,
            rep_event=rep_event,
            rom=self.candidate.rom,
        )

    def _update_bicep_curl(self, angle: float) -> tuple[str, str | None, bool]:
        config = self.config

        if angle >= config.down_threshold:
            if self.stage == "up":
                return self._complete_rep(angle)
            self.stage = "down"
            return "Arm extended. Curl upward with control.", None, False

        if self.stage == "down" and angle <= config.up_threshold:
            self.stage = "up"
            return "Good curl height. Lower slowly.", None, False

        if self.stage == "up":
            return "Lower with control until the arm is extended.", None, False

        self.stage = "moving"
        return "Keep the elbow near your side and continue the curl.", None, False

    def _update_shoulder_raise(self, angle: float) -> tuple[str, str | None, bool]:
        config = self.config

        if angle <= config.down_threshold:
            if self.stage == "up":
                return self._complete_rep(angle)
            self.stage = "down"
            return "Arm lowered. Raise toward shoulder height.", None, False

        if self.stage == "down" and angle >= config.up_threshold:
            self.stage = "up"
            return "Good shoulder height. Lower with control.", None, False

        if self.stage == "up":
            return "Lower smoothly back to the starting position.", None, False

        self.stage = "moving"
        return "Raise the arm without leaning or rushing.", None, False

    def _complete_rep(self, current_angle: float) -> tuple[str, str | None, bool]:
        config = self.config
        rom = self.candidate.rom
        min_angle = self.candidate.min_angle or 0.0
        max_angle = self.candidate.max_angle or 0.0
        mistake = self._classify_mistake(rom, min_angle, max_angle)

        self.reps += 1
        self.completed_roms.append(rom)

        if mistake:
            self.wrong_reps += 1
            self.mistakes.append(mistake)
            feedback = mistake
        else:
            self.correct_reps += 1
            feedback = "Good rep"

        self.stage = "down"
        self.candidate = RepCandidate(min_angle=current_angle, max_angle=current_angle)
        return feedback, mistake, True

    def _classify_mistake(self, rom: float, min_angle: float, max_angle: float) -> str | None:
        config = self.config

        if self.candidate.had_visibility_issue:
            return "Rep had poor camera visibility"

        if rom < config.min_rom:
            return "Incomplete range of motion"

        if self.exercise_key == "bicep_curl":
            if max_angle < config.target_max_angle:
                return "Do not start the curl before fully extending the elbow"
            if min_angle > config.target_min_angle:
                return "Curl a little higher to complete the repetition"
        else:
            if max_angle < config.target_max_angle:
                return "Raise the arm closer to shoulder height"
            if min_angle > config.target_min_angle:
                return "Lower fully before starting the next repetition"

        return None

    def _payload(
        self,
        angle: float | None,
        feedback: str,
        *,
        visibility_ok: bool,
        mistake: str | None = None,
        rep_event: bool = False,
        rom: float | None = None,
    ) -> dict[str, Any]:
        return {
            "exercise": self.exercise_key,
            "exercise_label": self.config.label,
            "angle": round(angle, 1) if angle is not None else None,
            "angle_name": self.config.angle_name,
            "stage": self.stage,
            "reps": self.reps,
            "correct_reps": self.correct_reps,
            "wrong_reps": self.wrong_reps,
            "feedback": feedback,
            "visibility_ok": visibility_ok,
            "mistake": mistake,
            "rep_event": rep_event,
            "rom": round(rom, 1) if rom is not None else None,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "exercise": self.exercise_key,
            "exercise_label": self.config.label,
            "stage": self.stage,
            "reps": self.reps,
            "correct_reps": self.correct_reps,
            "wrong_reps": self.wrong_reps,
            "completed_roms": list(self.completed_roms),
            "mistakes": list(self.mistakes),
        }


def list_exercises() -> list[dict[str, str]]:
    return [
        {
            "key": config.key,
            "label": config.label,
            "angle_name": config.angle_name,
            "instructions": config.instructions,
        }
        for config in EXERCISES.values()
    ]
