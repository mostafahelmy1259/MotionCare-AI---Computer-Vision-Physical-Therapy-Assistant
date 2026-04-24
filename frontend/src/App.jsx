import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, ClipboardCheck, Play, Square } from "lucide-react";
import CameraView from "./components/CameraView.jsx";
import MetricsPanel from "./components/MetricsPanel.jsx";
import FeedbackBox from "./components/FeedbackBox.jsx";
import SessionReport from "./components/SessionReport.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const WS_BASE =
  import.meta.env.VITE_WS_BASE_URL ||
  `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;

const DEFAULT_EXERCISES = [
  {
    key: "bicep_curl",
    label: "Seated Bicep Curl",
    angle_name: "right_elbow",
    instructions: "Sit upright, keep the right elbow close to the body, curl up, then lower with control.",
  },
  {
    key: "shoulder_raise",
    label: "Seated Shoulder Raise",
    angle_name: "right_shoulder",
    instructions: "Sit tall, raise the right arm toward shoulder height, then lower smoothly.",
  },
];

const initialMetrics = {
  exercise: "bicep_curl",
  exercise_label: "Seated Bicep Curl",
  angle: null,
  angle_name: "right_elbow",
  stage: "idle",
  reps: 0,
  correct_reps: 0,
  wrong_reps: 0,
  feedback: "Start a session when the patient is seated and visible.",
  visibility_ok: true,
  frame: null,
};

export default function App() {
  const [exercises, setExercises] = useState(DEFAULT_EXERCISES);
  const [selectedExercise, setSelectedExercise] = useState("bicep_curl");
  const [session, setSession] = useState(null);
  const [metrics, setMetrics] = useState(initialMetrics);
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState("Ready");
  const [isStarting, setIsStarting] = useState(false);
  const wsRef = useRef(null);
  const finishingRef = useRef(false);

  const activeExercise = useMemo(
    () => exercises.find((exercise) => exercise.key === selectedExercise) || exercises[0],
    [exercises, selectedExercise],
  );

  const isTracking = Boolean(session);

  useEffect(() => {
    fetch(`${API_BASE}/api/exercises`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then(setExercises)
      .catch(() => setExercises(DEFAULT_EXERCISES));
  }, []);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  async function startSession() {
    if (isTracking || isStarting) return;

    setIsStarting(true);
    setReport(null);
    setMetrics({
      ...initialMetrics,
      exercise: activeExercise.key,
      exercise_label: activeExercise.label,
      angle_name: activeExercise.angle_name,
      feedback: "Opening camera and starting pose tracking...",
    });
    setStatus("Starting");

    try {
      const response = await fetch(`${API_BASE}/api/session/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exercise: selectedExercise }),
      });

      if (!response.ok) {
        throw new Error("Could not start session");
      }

      const sessionData = await response.json();
      setSession(sessionData);
      connectWebSocket(sessionData.session_id);
    } catch (error) {
      setStatus("Backend unavailable");
      setMetrics((current) => ({
        ...current,
        visibility_ok: false,
        feedback: error.message || "Could not start the rehabilitation session.",
      }));
    } finally {
      setIsStarting(false);
    }
  }

  function connectWebSocket(sessionId) {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const socket = new WebSocket(`${WS_BASE}/ws/track/${sessionId}`);
    wsRef.current = socket;

    socket.onopen = () => setStatus("Tracking");

    socket.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        setStatus("Invalid tracking payload");
        return;
      }

      if (payload.type === "metrics") {
        setMetrics(payload);
      }

      if (payload.type === "status") {
        setStatus(payload.message);
      }

      if (payload.type === "error") {
        setStatus("Tracking error");
        setMetrics((current) => ({
          ...current,
          visibility_ok: false,
          feedback: payload.error,
        }));
        setSession(null);
        socket.close();
      }
    };

    socket.onclose = () => {
      wsRef.current = null;
      if (!finishingRef.current) {
        setSession(null);
      }
      setStatus((current) =>
        current === "Tracking" || current === "Opening camera and loading pose model." ? "Disconnected" : current,
      );
    };
  }

  async function finishSession() {
    if (!session) return;

    const sessionId = session.session_id;
    finishingRef.current = true;
    setStatus("Finishing");

    try {
      const response = await fetch(`${API_BASE}/api/session/${sessionId}/finish`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Could not finish session");
      }

      const reportData = await response.json();
      setReport(reportData);
      setStatus("Report ready");
    } catch (error) {
      setStatus("Finish failed");
      setMetrics((current) => ({
        ...current,
        visibility_ok: false,
        feedback: error.message || "Could not finish the session.",
      }));
    } finally {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setSession(null);
      finishingRef.current = false;
    }
  }

  function handleExerciseChange(event) {
    const nextExercise = event.target.value;
    setSelectedExercise(nextExercise);
    const exercise = exercises.find((item) => item.key === nextExercise);
    if (!isTracking && exercise) {
      setMetrics({
        ...initialMetrics,
        exercise: exercise.key,
        exercise_label: exercise.label,
        angle_name: exercise.angle_name,
      });
    }
  }

  return (
    <main className="app-shell">
      <section className="top-bar" aria-label="Session controls">
        <div>
          <p className="eyebrow">AI Rehabilitation Coach</p>
          <h1>Upper Body Seated Therapy</h1>
        </div>

        <div className="session-actions">
          <label className="exercise-select">
            <span>Exercise</span>
            <select value={selectedExercise} onChange={handleExerciseChange} disabled={isTracking}>
              {exercises.map((exercise) => (
                <option key={exercise.key} value={exercise.key}>
                  {exercise.label}
                </option>
              ))}
            </select>
          </label>

          <button className="primary-button" onClick={startSession} disabled={isTracking || isStarting}>
            <Play size={18} />
            Start Session
          </button>
          <button className="secondary-button" onClick={finishSession} disabled={!isTracking}>
            <Square size={18} />
            Finish Session
          </button>
        </div>
      </section>

      <section className="status-strip" aria-label="Session status">
        <div>
          <Activity size={18} />
          <span>{status}</span>
        </div>
        <p>{activeExercise?.instructions}</p>
      </section>

      <section className="dashboard-grid">
        <CameraView frame={metrics.frame} status={status} isTracking={isTracking} />

        <aside className="side-panel">
          <MetricsPanel metrics={metrics} />
          <FeedbackBox feedback={metrics.feedback} visibilityOk={metrics.visibility_ok} mistake={metrics.mistake} />
        </aside>
      </section>

      <section className="history-band" aria-label="Clinical report">
        <div className="section-heading">
          <ClipboardCheck size={20} />
          <h2>Session History & Clinical Report</h2>
        </div>
        <SessionReport report={report} liveMetrics={metrics} />
      </section>
    </main>
  );
}
