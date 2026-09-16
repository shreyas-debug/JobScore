"use client";

import { useState, useEffect } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import type { JobCard } from "@/lib/types";

interface SwipeCardProps {
  job: JobCard;
  onSwipe: (direction: "left" | "right") => void;
  externalSwipe?: "left" | "right" | null;
}

const SWIPE_THRESHOLD = 110;

function formatSalary(min: number | null, max: number | null): string {
  if (!min && !max) return "Competitive Salary";
  if (min && max) return `$${(min / 1000).toFixed(0)}k – $${(max / 1000).toFixed(0)}k`;
  if (min) return `From $${(min / 1000).toFixed(0)}k`;
  return `Up to $${(max! / 1000).toFixed(0)}k`;
}

export function SwipeCard({ job, onSwipe, externalSwipe }: SwipeCardProps) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-250, 250], [-20, 20]);
  const opacity = useTransform(x, [-280, -140, 0, 140, 280], [0.3, 1, 1, 1, 0.3]);

  const rightIndicatorOpacity = useTransform(x, [15, SWIPE_THRESHOLD], [0, 1]);
  const leftIndicatorOpacity = useTransform(x, [-SWIPE_THRESHOLD, -15], [1, 0]);

  function handleDragEnd(_: unknown, info: { offset: { x: number } }) {
    if (info.offset.x > SWIPE_THRESHOLD) {
      onSwipe("right");
    } else if (info.offset.x < -SWIPE_THRESHOLD) {
      onSwipe("left");
    }
  }

  // Handle external swipes (buttons/keyboard)
  useEffect(() => {
    if (externalSwipe) {
      const targetX = externalSwipe === "left" ? -500 : 500;
      animate(x, targetX, {
        type: "spring",
        stiffness: 350,
        damping: 28,
        onComplete: () => {
          onSwipe(externalSwipe);
        }
      });
    }
  }, [externalSwipe, x, onSwipe]);

  const [isFlipped, setIsFlipped] = useState(false);

  function handleClick() {
    // Only flip if not currently being dragged far
    if (Math.abs(x.get()) < 5) {
      setIsFlipped(!isFlipped);
    }
  }

  return (
    <motion.div
      data-testid="swipe-card"
      className="swipe-card"
      style={{ x, rotate, opacity }}
      drag="x"
      dragConstraints={{ left: -400, right: 400 }}
      onDragEnd={handleDragEnd}
      whileTap={{ cursor: "grabbing" }}
      initial={{ scale: 0.94, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 350, damping: 28 }}
      onClick={handleClick}
    >
      {/* Swipe Stamps */}
      <motion.div
        className="swipe-indicator swipe-indicator--right"
        style={{ opacity: rightIndicatorOpacity, zIndex: 10 }}
      >
        ♥ INTERESTED
      </motion.div>
      <motion.div
        className="swipe-indicator swipe-indicator--left"
        style={{ opacity: leftIndicatorOpacity, zIndex: 10 }}
      >
        ✕ PASS
      </motion.div>

      <motion.div
        className="swipe-card-inner"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ type: "spring", stiffness: 450, damping: 30 }}
      >
        {/* ── FRONT FACE ────────────────────────────────────────────── */}
        <div className="swipe-card-face">
          {/* Card Header */}
          <div className="swipe-card__header">
            {job.company_name && (
              <div className="swipe-card__company-row">
                <div className="swipe-card__company-avatar">
                  {job.company_name.charAt(0)}
                </div>
                <div>
                  <div className="swipe-card__company-name">{job.company_name}</div>
                  {job.company_industry && (
                    <div style={{ fontSize: "0.72rem", color: "var(--color-text-dim)" }}>
                      {job.company_industry}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
              <h2 className="swipe-card__title">{job.title}</h2>
              {job.seniority && (
                <span className="badge badge--primary" style={{ flexShrink: 0 }}>
                  {job.seniority}
                </span>
              )}
            </div>

            <div className="swipe-card__meta">
              <span style={{ fontWeight: 600, color: "var(--color-accent)" }}>
                {formatSalary(job.salary_min, job.salary_max)}
              </span>
              <span style={{ color: "var(--color-border-hover)" }}>•</span>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis" }} title={job.location || "Remote"}>
                {job.location || "Remote"}
              </span>
              {job.remote_ok && (
                <>
                  <span style={{ color: "var(--color-border-hover)" }}>•</span>
                  <span style={{ fontWeight: 600 }}>Remote OK</span>
                </>
              )}
            </div>
          </div>

          {/* Job Description (Truncated) */}
          {job.description && (
            <div className="swipe-card__description-wrapper">
              <p className="swipe-card__description">{job.description}</p>
            </div>
          )}

          {/* Skill Tags */}
          {job.required_skills && job.required_skills.length > 0 && (() => {
            const shown = job.required_skills.slice(0, 5);
            const remaining = job.required_skills.length - 5;
            return (
              <div style={{ marginTop: "auto" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)", textTransform: "uppercase", fontWeight: 700, marginBottom: 8 }}>
                  Skills
                </div>
                <div className="swipe-card__skills">
                  {shown.map((s) => (
                    <span
                      key={s.skill}
                      data-testid="skill-tag"
                      className="skill-tag"
                      title={s.level === "required" ? "Required" : "Preferred"}
                      style={s.level === "preferred" ? {
                        background: "transparent",
                        borderStyle: "dashed",
                        color: "var(--color-text-muted)"
                      } : {}}
                    >
                      {s.skill}
                    </span>
                  ))}
                  {remaining > 0 && (
                    <span className="skill-tag" style={{ color: "var(--color-text-dim)", background: "transparent", border: "none" }}>
                      +{remaining} more
                    </span>
                  )}
                </div>
              </div>
            );
          })()}
          
          <div style={{ textAlign: "center", marginTop: 8, color: "var(--color-text-dim)", fontSize: "0.75rem" }}>
            Tap to reveal details
          </div>
        </div>

        {/* ── BACK FACE ─────────────────────────────────────────────── */}
        <div className="swipe-card-face swipe-card-face--back">
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.2rem", margin: 0, color: "var(--color-text)" }}>
              About the Role
            </h3>
            <div style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", marginTop: 4 }}>
              {job.company_name} • {job.company_industry || "Technology"}
            </div>
          </div>

          <div style={{ flex: 1 }}>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.6, color: "var(--color-text)", whiteSpace: "pre-wrap", margin: 0 }}>
              {job.description || "No description provided."}
            </p>
          </div>

          {job.required_skills && job.required_skills.length > 0 && (() => {
            const required = job.required_skills.filter(s => s.level === "required");
            const preferred = job.required_skills.filter(s => s.level === "preferred");
            return (
              <div style={{ marginTop: 20 }}>
                {required.length > 0 && (
                  <>
                    <div style={{ fontSize: "0.72rem", color: "var(--color-text-dim)", textTransform: "uppercase", fontWeight: 700, marginBottom: 8 }}>
                      Required
                    </div>
                    <div className="swipe-card__skills" style={{ flexWrap: "wrap", marginBottom: 12 }}>
                      {required.map(s => (
                        <span key={s.skill} className="skill-tag">{s.skill}</span>
                      ))}
                    </div>
                  </>
                )}
                {preferred.length > 0 && (
                  <>
                    <div style={{ fontSize: "0.72rem", color: "var(--color-text-dim)", textTransform: "uppercase", fontWeight: 700, marginBottom: 8 }}>
                      Nice to Have
                    </div>
                    <div className="swipe-card__skills" style={{ flexWrap: "wrap" }}>
                      {preferred.map(s => (
                        <span key={s.skill} className="skill-tag" style={{ background: "transparent", borderStyle: "dashed", color: "var(--color-text-muted)" }}>
                          {s.skill}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            );
          })()}
        </div>
      </motion.div>
    </motion.div>
  );
}
