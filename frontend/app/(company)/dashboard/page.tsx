"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import type { DashboardResponse, JobListing } from "@/lib/types";
import { motion } from "framer-motion";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="stat-card">
      <div className="stat-card__value">{value}</div>
      <div className="stat-card__label">{label}</div>
      {sub && <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>{sub}</div>}
    </div>
  );
}

export default function CompanyDashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiClient.getDashboard().catch(() => null),
      apiClient.getJobs().catch(() => []),
    ]).then(([dashboardData, jobsData]) => {
      setData(dashboardData);
      setJobs(jobsData || []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <main className="page" style={{ justifyContent: "center" }}>
        <div style={{ maxWidth: 1000, width: "100%", margin: "0 auto", animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}>
           <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
             <div style={{ width: "40%", height: 32, background: "var(--color-border)", borderRadius: 6 }} />
             <div style={{ width: 140, height: 32, background: "var(--color-border)", borderRadius: 8 }} />
           </div>
           <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 20, marginBottom: 32 }}>
             {[1, 2, 3, 4].map((i) => (
               <div key={i} style={{ height: 120, background: "var(--color-border)", borderRadius: 16 }} />
             ))}
           </div>
           <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
             <div style={{ height: 300, background: "var(--color-border)", borderRadius: 16 }} />
             <div style={{ height: 300, background: "var(--color-border)", borderRadius: 16 }} />
           </div>
        </div>
        <style dangerouslySetInnerHTML={{ __html: `@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 0.2; } }` }} />
      </main>
    );
  }

  const avgScoreDisplay =
    data?.avg_score != null ? `${Math.round(data.avg_score * 100)}%` : "—";

  return (
    <main className="page">
      <div style={{ maxWidth: 1000, width: "100%", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
          <div>
            <h1 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "2rem", marginBottom: 8 }}>Recruiting Command Center</h1>
            <p style={{ color: "var(--color-text-dim)" }}>High-relevance matching overview. Zero spam, 100% threshold-cleared profiles.</p>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <Link href="/jobs" className="btn btn--secondary btn--sm">
              Manage Roles ({jobs.length})
            </Link>
            <Link href="/jobs/new" className="btn btn--primary btn--sm">
              + Post New Role
            </Link>
          </div>
        </div>

        {/* Top telemetry cards */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 20,
            marginBottom: 32,
          }}
        >
          <StatCard
            label="Candidates Evaluated"
            value={data?.total_swiped || 0}
            sub="Swipes on your roles"
          />
          <StatCard
            label="Mutual Matches"
            value={data?.total_matches || 0}
            sub="Cleared ≥60% score"
          />
          <StatCard
            label="Auto-Applications"
            value={data?.total_applied || 0}
            sub="Ready in your queue"
          />
          <StatCard
            label="Average Match Score"
            value={avgScoreDisplay}
            sub="Semantic & skill fit"
          />
        </motion.div>

        {/* Funnel & Active listings layout */}
        <motion.div 
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          {/* Funnel visualization */}
          <div
            style={{
              background: "var(--color-surface)",
              borderRadius: "var(--radius-card)",
              padding: 28,
              border: "1px solid var(--color-border)",
            }}
          >
            <h3 style={{ marginBottom: 16, fontFamily: "var(--font-display)" }}>Recruiting Funnel</h3>
            {data?.funnel && Object.keys(data.funnel).length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {Object.entries(data.funnel).map(([stage, count]) => (
                  <div key={stage} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.9rem" }}>
                      <span style={{ textTransform: "capitalize", color: "var(--color-text-muted)" }}>
                        {stage}
                      </span>
                      <strong>{count}</strong>
                    </div>
                    <div className="score-bar">
                      <motion.div
                        className="score-bar__fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, Math.max(8, (count / (data.total_applied || 1)) * 100))}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state" style={{ padding: "30px 0" }}>
                <span className="empty-state__icon">📊</span>
                <p>No applications in funnel yet. Post roles to attract candidates.</p>
              </div>
            )}
          </div>

          {/* Quick Active Jobs list */}
          <div
            style={{
              background: "var(--color-surface)",
              borderRadius: "var(--radius-card)",
              padding: 28,
              border: "1px solid var(--color-border)",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ fontFamily: "var(--font-display)" }}>Active Job Listings</h3>
              <Link href="/jobs" style={{ fontSize: "0.85rem", color: "var(--color-accent)", fontWeight: 600 }}>
                View all →
              </Link>
            </div>

            {jobs.length === 0 ? (
              <div className="empty-state" style={{ padding: "30px 0" }}>
                <span className="empty-state__icon">💼</span>
                <p>You haven&apos;t posted any jobs yet.</p>
                <Link href="/jobs/new" className="btn btn--primary btn--sm" style={{ marginTop: 8 }}>
                  Post First Job
                </Link>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {jobs.slice(0, 4).map((job) => (
                  <Link
                    href={`/jobs/${job.id}/candidates`}
                    key={job.id}
                    style={{ textDecoration: "none", color: "inherit" }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: "12px 16px",
                        background: "var(--color-surface-elevated)",
                        borderRadius: 12,
                        border: "1px solid var(--color-border)",
                        transition: "all 0.2s ease",
                        cursor: "pointer",
                      }}
                      className="hover-lift"
                    >
                      <div>
                        <h4 style={{ fontSize: "0.95rem" }}>{job.title}</h4>
                        <span style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>
                          {job.location || "Remote"} · {job.seniority || "Full-time"}
                        </span>
                      </div>
                      <span
                        className="btn btn--secondary btn--sm"
                        style={{ fontSize: "0.75rem", padding: "6px 12px" }}
                      >
                        Review Matches →
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </main>
  );
}
