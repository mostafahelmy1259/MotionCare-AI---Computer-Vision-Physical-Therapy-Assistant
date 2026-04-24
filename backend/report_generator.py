from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Any


def generate_report(session: Any) -> dict[str, Any]:
    snapshot = session.counter.snapshot()
    completed_roms = snapshot["completed_roms"]
    mistakes = snapshot["mistakes"]
    total_reps = snapshot["reps"]
    correct_reps = snapshot["correct_reps"]
    wrong_reps = snapshot["wrong_reps"]
    visibility_issues = sum(1 for sample in session.samples if not sample.get("visibility_ok", False))

    best_rom = max(completed_roms) if completed_roms else 0.0
    average_rom = mean(completed_roms) if completed_roms else 0.0
    common_mistake = _common_mistake(mistakes, visibility_issues)

    return {
        "session_id": session.session_id,
        "exercise": snapshot["exercise"],
        "exercise_label": snapshot["exercise_label"],
        "started_at": session.started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(session.duration_seconds, 1),
        "total_reps": total_reps,
        "correct_reps": correct_reps,
        "wrong_reps": wrong_reps,
        "best_rom": round(best_rom, 1),
        "average_rom": round(average_rom, 1),
        "common_mistake": common_mistake,
        "final_recommendation": _recommend(total_reps, correct_reps, wrong_reps, common_mistake, visibility_issues),
    }


def _common_mistake(mistakes: list[str], visibility_issues: int) -> str:
    if mistakes:
        return Counter(mistakes).most_common(1)[0][0]
    if visibility_issues:
        return "Intermittent camera visibility"
    return "None detected"


def _recommend(total_reps: int, correct_reps: int, wrong_reps: int, common_mistake: str, visibility_issues: int) -> str:
    if total_reps == 0:
        return "No complete repetitions were captured. Reposition the camera and complete slow, full repetitions."

    if visibility_issues > total_reps * 2:
        return "Improve camera placement before progressing. Keep the right shoulder, elbow, wrist, and hip visible."

    accuracy = correct_reps / total_reps if total_reps else 0.0
    if accuracy >= 0.85:
        return "Form quality is strong. Continue with the same movement and progress volume only if pain-free."

    if wrong_reps > correct_reps:
        return f"Prioritize quality before adding reps. Main focus: {common_mistake.lower()}."

    return f"Continue practicing with controlled tempo. Watch for: {common_mistake.lower()}."
