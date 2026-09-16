"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState, useEffect } from "react";
import { SwipeCard } from "./SwipeCard";
import type { JobCard } from "@/lib/types";

interface SwipeDeckProps {
  jobs: JobCard[];
  externalSwipe?: { id: string, direction: "left" | "right" } | null;
  onSwipe: (jobId: string, direction: "left" | "right") => Promise<void>;
  onEmpty?: () => void;
}

export function SwipeDeck({ jobs, externalSwipe, onSwipe, onEmpty }: SwipeDeckProps) {
  const [swiping, setSwiping] = useState(false);

  async function handleSwipe(direction: "left" | "right") {
    if (swiping || jobs.length === 0) return;
    const current = jobs[0];
    setSwiping(true);
    try {
      await onSwipe(current.id, direction);
    } finally {
      setSwiping(false);
    }
    if (jobs.length <= 1) {
      onEmpty?.();
    }
  }

  if (jobs.length === 0) {
    return (
      <div className="swipe-deck swipe-deck--empty" data-testid="empty-feed" style={{ border: "none", background: "transparent", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ padding: "48px 32px", textAlign: "center", maxWidth: 400, width: "100%", display: "flex", flexDirection: "column", gap: 16 }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.5rem", color: "var(--color-text)", margin: 0 }}>
            You're all caught up
          </h3>
          <p style={{ fontSize: "0.95rem", color: "var(--color-text-muted)", margin: 0 }}>
            You've reviewed all active roles matching your current criteria. Broaden your search to see more.
          </p>
          <div style={{ marginTop: 12 }}>
            <a href="/profile" className="btn btn--primary" style={{ width: "100%", justifyContent: "center" }}>
              Update Preferences
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="swipe-deck">
      <AnimatePresence>
        {/* Render top 2 cards for seamless stack depth */}
        {jobs.slice(0, 2).map((job, idx) => (
          <motion.div
            key={job.id}
            className="swipe-card-layer"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              zIndex: 2 - idx,
              pointerEvents: idx === 0 ? "auto" : "none",
            }}
            initial={{ scale: 0.94, y: 14 }}
            animate={{ scale: 1 - idx * 0.04, y: idx * 14 }}
            exit={{ opacity: 0, transition: { duration: 0.2 } }}
            transition={{ type: "spring", stiffness: 350, damping: 28 }}
          >
            {idx === 0 && (
              <SwipeCard 
                job={job} 
                onSwipe={handleSwipe} 
                externalSwipe={externalSwipe?.id === job.id ? externalSwipe.direction : null}
              />
            )}
            {idx === 1 && (
              <div className="swipe-card swipe-card--ghost" aria-hidden="true" />
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
