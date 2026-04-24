import { Gauge, Repeat2, Target, XCircle } from "lucide-react";

function formatAngle(angle) {
  return angle === null || angle === undefined ? "--" : `${Number(angle).toFixed(1)} deg`;
}

export default function MetricsPanel({ metrics }) {
  const cards = [
    {
      label: "Current Angle",
      value: formatAngle(metrics.angle),
      detail: metrics.angle_name?.replace("_", " ") || "right elbow",
      icon: Gauge,
    },
    {
      label: "Total Reps",
      value: metrics.reps ?? 0,
      detail: `Stage: ${metrics.stage || "idle"}`,
      icon: Repeat2,
    },
    {
      label: "Correct Reps",
      value: metrics.correct_reps ?? 0,
      detail: "Completed with target ROM",
      icon: Target,
    },
    {
      label: "Wrong Reps",
      value: metrics.wrong_reps ?? 0,
      detail: "Needs correction",
      icon: XCircle,
    },
  ];

  return (
    <section className="metrics-panel" aria-label="Real-time rehabilitation metrics">
      <div className="panel-title">
        <Gauge size={20} />
        <h2>Real-Time Metrics</h2>
      </div>

      <div className="metric-grid">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article className="metric-card" key={card.label}>
              <div className="metric-icon">
                <Icon size={18} />
              </div>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
              <p>{card.detail}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
