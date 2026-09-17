"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import type { JobListing } from "@/lib/types";
import { motion } from "framer-motion";

export default function JobListingsPage() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.getJobs()
      .then((data) => {
        setJobs(data || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  async function toggleStatus(job: JobListing) {
    try {
      const updated = await apiClient.patchJob(job.id, { is_active: !job.is_active });
      setJobs((prev) => prev.map((j) => (j.id === job.id ? updated : j)));
    } catch (err) {
      console.error("Failed to toggle status:", err);
    }
  }

  if (loading) {
    return (
      <main className="page" style={{ justifyContent: "center" }}>
        <div style={{ maxWidth: 960, width: "100%", margin: "0 auto", display: "flex", flexDirection: "column", gap: 16 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="card" style={{ padding: "20px 24px", animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
                  <div style={{ width: "40%", height: 20, background: "var(--color-border)", borderRadius: 4 }} />
                  <div style={{ width: "60%", height: 14, background: "var(--color-border)", borderRadius: 4 }} />
                  <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                     <div style={{ width: 60, height: 24, background: "var(--color-border)", borderRadius: 12 }} />
                     <div style={{ width: 80, height: 24, background: "var(--color-border)", borderRadius: 12 }} />
                  </div>
                </div>
                <div style={{ display: "flex", gap: 12 }}>
                  <div style={{ width: 80, height: 32, background: "var(--color-border)", borderRadius: 8 }} />
                  <div style={{ width: 140, height: 32, background: "var(--color-border)", borderRadius: 8 }} />
                </div>
              </div>
            </div>
          ))}
        </div>
        <style dangerouslySetInnerHTML={{ __html: `@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 0.2; } }` }} />
      </main>
    );
  }

  return (
    <main className="page">
      <div style={{ maxWidth: 960, width: "100%", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
          <div>
            <h1 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "2rem", marginBottom: 8 }}>Job Listings</h1>
            <p style={{ color: "var(--color-text-dim)" }}>Manage postings. Our matching engine pairs cleared candidates automatically.</p>
          </div>
          <Link href="/jobs/new" className="btn btn--primary btn--sm">
            + Post New Role
          </Link>
        </div>

        {jobs.length === 0 ? (
          <div
            className="empty-state"
            style={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-card)",
              padding: 48,
            }}
          >
            <span className="empty-state__icon">💼</span>
            <h2>No job listings posted yet</h2>
            <p>Create your first job listing to begin receiving qualified, threshold-gated applicants.</p>
            <Link href="/jobs/new" className="btn btn--primary" style={{ marginTop: 12 }}>
              Post a Job →
            </Link>
          </div>
        ) : (
          <motion.div 
            style={{ display: "flex", flexDirection: "column", gap: 16 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ staggerChildren: 0.1 }}
          >
            {jobs.map((job) => (
              <motion.div
                key={job.id}
                className="card"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  flexDirection: "row",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "20px 24px",
                }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <h3 style={{ fontSize: "1.2rem", fontFamily: "var(--font-display)", fontWeight: 600 }}>{job.title}</h3>
                    <span className={`badge ${job.is_active ? "badge--success" : "badge--danger"}`}>
                      {job.is_active ? "Active" : "Paused"}
                    </span>
                    {job.seniority && (
                      <span className="badge badge--primary">{job.seniority}</span>
                    )}
                  </div>

                  <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
                    {job.location || "Remote"} {job.remote_ok ? "· Remote OK" : ""} · Min {job.min_years_experience} yrs exp
                    {job.salary_min && job.salary_max ? ` · $${job.salary_min.toLocaleString()} – $${job.salary_max.toLocaleString()}` : ""}
                  </p>

                  {job.required_skills && job.required_skills.length > 0 && (
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
                      {job.required_skills.map((s) => (
                        <span key={s.skill} className="skill-tag" style={{ fontSize: "0.75rem", padding: "2px 8px" }}>
                          {s.skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <button
                    onClick={() => toggleStatus(job)}
                    className="btn btn--outline btn--sm"
                    style={{ fontSize: "0.8rem" }}
                  >
                    {job.is_active ? "Pause" : "Activate"}
                  </button>
                  <Link
                    href={`/jobs/${job.id}/candidates`}
                    className="btn btn--primary btn--sm"
                  >
                    Review Candidates →
                  </Link>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </main>
  );
}
