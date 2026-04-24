import { Camera } from "lucide-react";

export default function CameraView({ frame, status, isTracking }) {
  return (
    <section className="camera-panel" aria-label="Live camera feed">
      <div className="panel-title">
        <Camera size={20} />
        <h2>Live Camera</h2>
      </div>

      <div className="camera-frame">
        {frame ? (
          <img src={frame} alt="Live pose tracking feed" />
        ) : (
          <div className="camera-placeholder">
            <Camera size={42} />
            <p>{isTracking ? "Waiting for webcam frames..." : "Camera feed appears after session start"}</p>
          </div>
        )}
      </div>

      <div className="camera-footer">
        <span className={isTracking ? "dot active" : "dot"} />
        <span>{status}</span>
      </div>
    </section>
  );
}
