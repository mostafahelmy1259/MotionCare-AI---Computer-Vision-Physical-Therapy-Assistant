import { AlertTriangle, CheckCircle2 } from "lucide-react";

export default function FeedbackBox({ feedback, visibilityOk, mistake }) {
  const isPositive = visibilityOk && !mistake;

  return (
    <section className={`feedback-box ${isPositive ? "good" : "needs-work"}`} aria-label="Therapist feedback">
      <div className="feedback-icon">{isPositive ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}</div>
      <div>
        <h2>Therapist Feedback</h2>
        <p>{feedback || "Awaiting movement data."}</p>
      </div>
    </section>
  );
}
