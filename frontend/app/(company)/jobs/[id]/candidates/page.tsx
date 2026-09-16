"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import type { Application } from "@/lib/types";

export default function JobCandidatesReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;

  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    apiClient.getJobApplications(jobId)
      .then((data) => {
        setApplications(data || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [jobId]);

  async function handleStatusUpdate(appId: string, newStatus: "interview" | "rejected") {
    setUpdatingId(appId);
    try {
      const updated = await apiClient.updateApplicationStatus(appId, newStatus);
      setApplications((prev) =>
        prev.map((a) => (a.id === appId ? { ...a, status: updated.status } : a))
      );
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setUpdatingId(null);
    }
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case "interview":
        return <span className="badge badge--success">Interview Invited</span>;
      case "rejected":
        return <span className="badge badge--danger">Passed</span>;
      case "submitted":
      case "viewed":
      default:
        return <span className="badge badge--primary">Awaiting Review</span>;
    }
  }

  if (loading) {
    return (
      <main className="page" style={{ justifyContent: "center" }}>
        <p>Loading matched candidates…</p>
      </main>
    );
  }

  return (
    <main className="page">
      <div style={{ maxWidth: 840, width: "100%", margin: "0 auto" }}>
        <div style={{ marginBottom: 24 }}>
          <Link href="/jobs" style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
            ← Back to All Roles
          </Link>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
            <div>
              <h1>Pre-Filtered Applicants</h1>
              <p>
                Every candidate below cleared your minimum 60% match score threshold on their
                right-swipe.
              </p>
            </div>
            <span className="badge badge--primary" style={{ padding: "8px 14px" }}>
              {applications.length} Matched Profiles
            </span>
          </div>
        </div>

        {applications.length === 0 ? (
          <div
            className="empty-state"
            style={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-card)",
              padding: 48,
            }}
          >
            <span className="empty-state__icon">⏳</span>
            <h2>No matched applicants yet</h2>
            <p>
              Candidates who pass hard filters (years of experience, location, salary) and clear
              the 60% score threshold will land directly in this queue.
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {applications.map((app) => (
              <div
                key={app.id}
                className="card"
                style={{
                  padding: 28,
                  gap: 16,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                      <h3 style={{ fontSize: "1.25rem" }}>
                        Candidate #{app.candidate_id.slice(0, 8)}
                      </h3>
                      {getStatusBadge(app.status)}
                    </div>
                    <span style={{ fontSize: "0.8rem", color: "var(--color-text-dim)" }}>
                      Application ID: {app.id} · Applied {
                        (() => {
                          const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
                          const diff = (new Date(app.created_at).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24);
                          return Math.abs(diff) < 1 ? "today" : rtf.format(Math.round(diff), 'day');
                        })()
                      }
                    </span>
                  </div>

                  <div
                    style={{
                      background: "rgba(108, 99, 255, 0.12)",
                      border: "1px solid var(--color-accent)",
                      borderRadius: 12,
                      padding: "6px 14px",
                      textAlign: "center",
                    }}
                  >
                    <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", display: "block" }}>
                      Threshold
                    </span>
                    <span style={{ fontWeight: 800, color: "var(--color-accent)" }}>Cleared ≥ 60%</span>
                  </div>
                </div>

                <p style={{ fontSize: "0.9rem", color: "var(--color-text-muted)" }}>
                  Verified profile with matching semantic embedding and required skill overlap.
                </p>

                {/* Recruiter Action Controls */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: 12,
                    paddingTop: 12,
                    borderTop: "1px solid var(--color-border)",
                  }}
                >
                  <button
                    disabled={updatingId === app.id || app.status === "rejected"}
                    onClick={() => handleStatusUpdate(app.id, "rejected")}
                    className="btn btn--outline btn--sm"
                    style={{
                      color: app.status === "rejected" ? "var(--color-text-dim)" : "var(--color-danger)",
                    }}
                  >
                    {app.status === "rejected" ? "Passed" : "Pass / Reject"}
                  </button>

                  <button
                    disabled={updatingId === app.id || app.status === "interview"}
                    onClick={() => handleStatusUpdate(app.id, "interview")}
                    className="btn btn--success btn--sm"
                  >
                    {app.status === "interview" ? "✓ Invited to Interview" : "Invite to Interview →"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
