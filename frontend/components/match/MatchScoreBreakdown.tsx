import type { MatchBreakdown } from "@/lib/types";

interface Props {
  breakdown: MatchBreakdown;
}

const COMPONENTS = [
  {
    key: "embedding_similarity" as const,
    label: "Skills (Semantic)",
    weight: 0.5,
    description: "How well your experience semantically matches the role",
  },
  {
    key: "skill_overlap" as const,
    label: "Skill Tags",
    weight: 0.25,
    description: "Required skills weighted 3x over preferred",
  },
  {
    key: "experience_fit" as const,
    label: "Experience",
    weight: 0.15,
    description: "Your years of experience vs the minimum required",
  },
  {
    key: "salary_overlap" as const,
    label: "Salary",
    weight: 0.1,
    description: "How well your salary expectations align with the range",
  },
];

function ScoreBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="score-bar" aria-label={`${pct}%`}>
      <div className="score-bar__fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function MatchScoreBreakdown({ breakdown }: Props) {
  const bd = breakdown.score_breakdown;
  const total = Math.round(breakdown.score * 100);
  const usedFallback = bd?.used_embedding_fallback === true;

  return (
    <div className="match-breakdown" data-testid="score-breakdown">
      <div className="match-breakdown__header">
        <h2 className="match-breakdown__total-label">Match Score</h2>
        <div className="match-breakdown__total-score">{total}%</div>
      </div>

      {usedFallback && (
        <div
          role="alert"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: "rgba(251, 191, 36, 0.10)",
            border: "1px solid rgba(251, 191, 36, 0.35)",
            borderRadius: 10,
            padding: "8px 12px",
            marginBottom: 12,
            fontSize: "0.78rem",
            color: "var(--color-text-muted)",
            lineHeight: 1.4,
          }}
        >
          <span style={{ fontSize: "1rem" }}>&#9888;</span>
          <span>
            Semantic score used a baseline estimate — your profile embedding is still generating.
            Update your profile in a moment to get the full score.
          </span>
        </div>
      )}

      <div className="match-breakdown__components">
        {COMPONENTS.map(({ key, label, weight, description }) => {
          const rawValue = bd?.[key] ?? 0;
          const contribution = Math.round(rawValue * weight * 100);
          const isEmbedding = key === "embedding_similarity";

          return (
            <div key={key} className="match-breakdown__item" data-testid={`breakdown-${key}`}>
              <div className="match-breakdown__item-header">
                <span className="match-breakdown__item-label">
                  {label}
                  {isEmbedding && usedFallback && (
                    <span
                      title="Estimated — update your profile to recompute"
                      style={{ marginLeft: 6, fontSize: "0.7rem", color: "#f59e0b", fontWeight: 700 }}
                    >
                      ~est
                    </span>
                  )}
                </span>
                <span className="match-breakdown__item-weight">x{weight}</span>
                <span className="match-breakdown__item-score">{contribution}pts</span>
              </div>
              <ScoreBar value={rawValue} />
              <p className="match-breakdown__item-description">{description}</p>
            </div>
          );
        })}
      </div>

    </div>
  );
}
