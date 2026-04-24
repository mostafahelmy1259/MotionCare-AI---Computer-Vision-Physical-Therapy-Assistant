import { BarChart3, CheckCircle2, ClipboardList, RotateCcw, XCircle } from "lucide-react";

export default function SessionReport({ report, liveMetrics }) {
  if (!report) {
    return (
      <div className="report-empty">
        <div>
          <ClipboardList size={24} />
          <strong>Current session preview</strong>
        </div>
        <p>
          Total {liveMetrics.reps ?? 0} · Correct {liveMetrics.correct_reps ?? 0} · Wrong{" "}
          {liveMetrics.wrong_reps ?? 0}
        </p>
      </div>
    );
  }

  const reportItems = [
    { label: "Total reps", value: report.total_reps, icon: RotateCcw },
    { label: "Correct reps", value: report.correct_reps, icon: CheckCircle2 },
    { label: "Wrong reps", value: report.wrong_reps, icon: XCircle },
    { label: "Best ROM", value: `${report.best_rom} deg`, icon: BarChart3 },
    { label: "Average ROM", value: `${report.average_rom} deg`, icon: BarChart3 },
  ];

  return (
    <div className="report-panel">
      <div className="report-grid">
        {reportItems.map((item) => {
          const Icon = item.icon;
          return (
            <article className="report-card" key={item.label}>
              <Icon size={18} />
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </article>
          );
        })}
      </div>

      <div className="report-summary">
        <div>
          <span>Common mistake</span>
          <strong>{report.common_mistake}</strong>
        </div>
        <div>
          <span>Final recommendation</span>
          <p>{report.final_recommendation}</p>
        </div>
      </div>
    </div>
  );
}
