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
    description: "How many required skills appear in your profile",
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

  return (
    <div className="match-breakdown" data-testid="score-breakdown">
      <div className="match-breakdown__header">
        <h2 className="match-breakdown__total-label">Match Score</h2>
        <div className="match-breakdown__total-score">{total}%</div>
      </div>

      <div className="match-breakdown__components">
        {COMPONENTS.map(({ key, label, weight, description }) => {
          const rawValue = bd?.[key] ?? 0;
          const contribution = Math.round(rawValue * weight * 100);

          return (
            <div key={key} className="match-breakdown__item" data-testid={`breakdown-${key}`}>
              <div className="match-breakdown__item-header">
                <span className="match-breakdown__item-label">{label}</span>
                <span className="match-breakdown__item-weight">×{weight}</span>
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
