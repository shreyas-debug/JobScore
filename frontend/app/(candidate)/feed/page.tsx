"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { SwipeDeck } from "@/components/swipe/SwipeDeck";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import type { JobCard, FeedResponse } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";

interface MatchCelebration {
  jobTitle: string;
}

export default function FeedPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<JobCard[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dailyCapReached, setDailyCapReached] = useState(false);
  const [matchCelebration, setMatchCelebration] = useState<MatchCelebration | null>(null);
  const [externalSwipe, setExternalSwipe] = useState<{ id: string, direction: "left" | "right" } | null>(null);

  function triggerSwipe(direction: "left" | "right") {
    if (jobs.length > 0 && !externalSwipe) {
      setExternalSwipe({ id: jobs[0].id, direction });
    }
  }

  const loadFeed = useCallback(async (cursor?: string) => {
    if (!cursor) setLoading(true);
    setError(null);
    try {
      const data = (await apiClient.getFeed(cursor)) as FeedResponse;
      setJobs((prev) => (cursor ? [...prev, ...data.items] : data.items));
      setNextCursor(data.next_cursor);
    } catch (e: any) {
      if (e.message?.includes("429") || e.message?.toLowerCase().includes("daily")) {
        setDailyCapReached(true);
      } else {
        setError(e.message || "Failed to load job feed.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  async function handleSwipe(jobId: string, direction: "left" | "right") {
    setExternalSwipe(null);
    const swipedJob = jobs.find((j) => j.id === jobId);

    // Optimistically remove the job from the local deck
    setJobs((prev) => prev.filter((j) => j.id !== jobId));

    try {
      const res = await apiClient.swipe(jobId, direction);
      if (res.matched && swipedJob) {
        setMatchCelebration({
          jobTitle: swipedJob.title,
        });
        setTimeout(() => setMatchCelebration(null), 1300);
      }
    } catch (err: any) {
      if (err.message?.includes("429") || err.message?.toLowerCase().includes("cap")) {
        setDailyCapReached(true);
      } else {
        // Conflict (already swiped) is fine — silently ignore
        if (!err.message?.includes("already swiped")) {
          console.warn("Swipe error:", err);
        }
      }
    }

    // Pre-fetch more cards when running low
    if (jobs.length <= 3 && nextCursor) {
      loadFeed(nextCursor);
    }
  }

  // Keyboard controls
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (jobs.length === 0 || matchCelebration || dailyCapReached || externalSwipe) return;
      if (e.key === "ArrowLeft") triggerSwipe("left");
      else if (e.key === "ArrowRight") triggerSwipe("right");
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [jobs, matchCelebration, dailyCapReached, externalSwipe]);

  if (dailyCapReached) {
    return (
      <main className="page" style={{ justifyContent: "center" }}>
        <div
          className="empty-state"
          style={{
            maxWidth: 480,
            background: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-card)",
            padding: 40,
          }}
        >
          <span className="empty-state__icon">🛑</span>
          <h2>Daily Swipe Cap Reached</h2>
          <p>
            Jobscore enforces a daily swipe limit to preserve signal quality. You&apos;ve
            evaluated your top recommendations for today!
          </p>
          <div style={{ marginTop: 16 }}>
            <Link href="/matches" className="btn btn--primary">
              View Your Matches →
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (loading && jobs.length === 0) {
    return (
      <main className="page" style={{ justifyContent: "center" }}>
        <div className="swipe-deck">
          <div className="swipe-card swipe-card--ghost" style={{ animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}>
            <div className="swipe-card__header">
              <div className="swipe-card__company-row">
                <div className="swipe-card__company-avatar" style={{ background: "var(--color-border)" }} />
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <div style={{ width: 120, height: 16, background: "var(--color-border)", borderRadius: 4 }} />
                  <div style={{ width: 80, height: 12, background: "var(--color-border)", borderRadius: 4 }} />
                </div>
              </div>
              <div style={{ width: 200, height: 28, background: "var(--color-border)", borderRadius: 6, marginTop: 12 }} />
              <div style={{ width: 140, height: 16, background: "var(--color-border)", borderRadius: 4, marginTop: 12 }} />
            </div>
            <div className="swipe-card__description-wrapper" style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ width: "100%", height: 14, background: "var(--color-border)", borderRadius: 4 }} />
              <div style={{ width: "90%", height: 14, background: "var(--color-border)", borderRadius: 4 }} />
              <div style={{ width: "40%", height: 14, background: "var(--color-border)", borderRadius: 4 }} />
            </div>
          </div>
        </div>
        <style dangerouslySetInnerHTML={{ __html: `@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 0.2; } }` }} />
      </main>
    );
  }

  if (error) {
    return (
      <main className="page" style={{ justifyContent: "center" }}>
        <div className="empty-state">
          <span className="empty-state__icon">⚠️</span>
          <h3>Something went wrong</h3>
          <p>{error}</p>
          <button onClick={() => loadFeed()} className="btn btn--secondary" style={{ marginTop: 12 }}>
            Try Again
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="page" style={{ 
      flex: 1, 
      overflow: "hidden", 
      display: "flex", 
      flexDirection: "column", 
      padding: "20px 0"
    }}>
      {jobs.length > 0 && (
        <div style={{ textAlign: "center", marginBottom: 16 }}>
          <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--color-accent)", fontWeight: 700 }}>
            Curated Deck
          </span>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "1.6rem", margin: "4px 0" }}>Find Your Match</h1>
          <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", margin: 0 }}>Swipe right to express interest · Swipe left to pass</p>
        </div>
      )}

      <div style={{ position: "relative", width: "100%", display: "flex", justifyContent: "center", flex: 1, minHeight: 0 }}>
        <SwipeDeck
          jobs={jobs}
          externalSwipe={externalSwipe}
          onSwipe={handleSwipe}
          onEmpty={() => nextCursor && loadFeed(nextCursor)}
        />
      </div>

      {/* Manual Action Buttons */}
      {jobs.length > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 24,
            marginTop: 12,
          }}
        >
          <button
            onClick={() => triggerSwipe("left")}
            className="btn btn--outline"
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              padding: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.4rem",
              color: "var(--color-danger)",
              borderColor: "var(--color-danger)",
            }}
            title="Pass (Left Arrow)"
          >
            ✕
          </button>

          <span style={{ fontSize: "0.85rem", color: "var(--color-text-dim)" }}>
            Use ← → arrow keys
          </span>

          <button
            onClick={() => triggerSwipe("right")}
            className="btn btn--primary"
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              padding: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.4rem",
            }}
            title="Express Interest (Right Arrow)"
          >
            ♥
          </button>
        </div>
      )}

      {/* ── Match Celebration Modal ───────────────────────────────────────── */}
      <AnimatePresence>
        {matchCelebration && (
          <div style={{ 
            position: "absolute", 
            inset: 0,
            background: "rgba(245, 241, 232, 0.2)",
            backdropFilter: "blur(4px)",
            WebkitBackdropFilter: "blur(4px)",
            pointerEvents: "none", 
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}>
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: -20 }}
              transition={{ type: "spring", bounce: 0.5 }}
              style={{
                padding: "16px 32px",
                borderRadius: "var(--radius-pill)",
                background: "var(--color-accent)",
                color: "#fff",
                boxShadow: "0 10px 40px rgba(193, 99, 61, 0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <h2 style={{ 
                fontFamily: "var(--font-display)", 
                fontSize: "1.6rem", 
                fontWeight: 700, 
                margin: 0,
                letterSpacing: "-0.02em" 
              }}>
                It's a match!
              </h2>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </main>
  );
}
