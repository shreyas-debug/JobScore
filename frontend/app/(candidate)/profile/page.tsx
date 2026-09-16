"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { MatchScoreBreakdown } from "@/components/match/MatchScoreBreakdown";
import type { Candidate, Match, MatchBreakdown } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";

export default function CandidateProfileDashboardPage() {
  const router = useRouter();
  const { candidateProfile, refreshCandidateProfile } = useAuth();
  
  // Tab State
  const [activeTab, setActiveTab] = useState<"preferences" | "matches">("matches");

  // --- PREFERENCES STATE ---
  const [name, setName] = useState("");
  const [summary, setSummary] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [yearsExperience, setYearsExperience] = useState(0);
  const [salaryMin, setSalaryMin] = useState<number | null>(null);
  const [salaryMax, setSalaryMax] = useState<number | null>(null);
  const [location, setLocation] = useState("");
  const [remoteOk, setRemoteOk] = useState(true);

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // --- MATCHES STATE ---
  const [matches, setMatches] = useState<Match[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [breakdowns, setBreakdowns] = useState<Record<string, MatchBreakdown>>({});
  const [loadingMatches, setLoadingMatches] = useState(true);

  // Load Profile
  useEffect(() => {
    if (candidateProfile) {
      setName(candidateProfile.name || "");
      setSummary(candidateProfile.resume_summary || "");
      setSkills(candidateProfile.skills || []);
      setYearsExperience(candidateProfile.years_experience || 0);
      setSalaryMin(candidateProfile.desired_salary_min);
      setSalaryMax(candidateProfile.desired_salary_max);
      setLocation(candidateProfile.location || "");
      setRemoteOk(candidateProfile.remote_ok ?? true);
    }
  }, [candidateProfile]);

  // Load Matches
  useEffect(() => {
    if (activeTab === "matches") {
      setLoadingMatches(true);
      apiClient.getMatches().then((data: any) => {
        setMatches(data || []);
        setLoadingMatches(false);
      }).catch(() => setLoadingMatches(false));
    }
  }, [activeTab]);

  // --- PREFERENCES LOGIC ---
  function addSkill() {
    const parts = newSkill.split(",").map((s) => s.trim()).filter(Boolean);
    const fresh = parts.filter((p) => !skills.includes(p));
    if (fresh.length > 0) {
      setSkills([...skills, ...fresh]);
      setNewSkill("");
    }
  }

  function removeSkill(toRemove: string) {
    setSkills(skills.filter((s) => s !== toRemove));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await apiClient.updateCandidateProfile({
        name,
        resume_summary: summary,
        skills,
        years_experience: yearsExperience,
        desired_salary_min: salaryMin,
        desired_salary_max: salaryMax,
        location,
        remote_ok: remoteOk,
      });
      await refreshCandidateProfile();
      router.refresh(); 
      router.push("/feed");
    } catch (err: any) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  }

  async function handleResetSwipes() {
    if (!confirm("Are you sure? This will delete all your swipes and matches, giving you a fresh deck for testing.")) return;
    try {
      await apiClient.resetSwipes();
      setSuccessMsg("Test deck reset successfully! Head back to the Feed.");
    } catch (err: any) {
      setError(err.message || "Failed to reset swipes.");
    }
  }

  // --- MATCHES LOGIC ---
  async function toggleExpand(matchId: string) {
    if (expandedId === matchId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(matchId);
    if (!breakdowns[matchId]) {
      try {
        const bd = (await apiClient.getMatchBreakdown(matchId)) as MatchBreakdown;
        setBreakdowns((prev) => ({ ...prev, [matchId]: bd }));
      } catch (err) {
        console.error("Failed to load breakdown:", err);
      }
    }
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case "interview": return <span className="badge badge--success">Interview Invited</span>;
      case "rejected": return <span className="badge badge--danger">Passed</span>;
      case "applied":
      case "submitted": return <span className="badge badge--primary">Application Submitted</span>;
      default: return <span className="badge badge--warning">{status}</span>;
    }
  }

  return (
    <main className="page">
      <div style={{ maxWidth: 680, width: "100%", margin: "0 auto" }}>
        
        {/* Dashboard Header & Tabs */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32, paddingBottom: 16, borderBottom: "1px solid var(--color-border)" }}>
          <h1 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "2rem", margin: 0 }}>Candidate Dashboard</h1>
          
          <div>
            <button 
              onClick={() => setActiveTab(activeTab === "matches" ? "preferences" : "matches")}
              className="btn btn--secondary btn--sm"
              style={{ borderRadius: 8, padding: "8px 16px" }}
            >
              {activeTab === "matches" ? "⚙️ Update Preferences" : "← Back to Matches"}
            </button>
          </div>
        </div>

        {/* --- TAB CONTENT: PREFERENCES --- */}
        {activeTab === "preferences" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
            {successMsg && (
              <div style={{ background: "rgba(34, 197, 94, 0.12)", border: "1px solid var(--color-success)", color: "var(--color-success)", padding: "12px 16px", borderRadius: 12, fontSize: "0.9rem", marginBottom: 20 }}>
                ✓ {successMsg}
              </div>
            )}

            {error && (
              <div style={{ background: "rgba(239, 68, 68, 0.12)", border: "1px solid var(--color-danger)", color: "var(--color-danger)", padding: "12px 16px", borderRadius: 12, fontSize: "0.9rem", marginBottom: 20 }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-card)", padding: 32, boxShadow: "var(--shadow-card)", display: "flex", flexDirection: "column", gap: 20 }}>
                
                <div>
                  <label className="form__label">Full Name</label>
                  <input type="text" className="form__input" style={{ width: "100%", marginTop: 6 }} value={name} onChange={(e) => setName(e.target.value)} required />
                </div>

                <div>
                  <label className="form__label">Resume Summary / Bio</label>
                  <textarea className="form__input" rows={4} style={{ width: "100%", marginTop: 6, resize: "vertical" }} value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="Overview of your technical strengths and background…" />
                </div>

                <div>
                  <label className="form__label">Skills</label>
                  <div style={{ marginTop: 8, marginBottom: 12 }}>
                    <div className="skill-chips">
                      {skills.map((skill) => (
                        <span key={skill} className="skill-chip skill-chip--highlight">
                          {skill}
                          <button type="button" onClick={() => removeSkill(skill)} className="skill-chip__remove">✕</button>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="skill-input-container">
                    <input type="text" className="form__input" style={{ flex: 1 }} placeholder="e.g. React, TypeScript, Node.js — press Enter or comma to add" value={newSkill} onChange={(e) => setNewSkill(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addSkill(); } }} />
                    <button type="button" onClick={addSkill} className="btn btn--secondary btn--sm">+ Add</button>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                  <div>
                    <label className="form__label">Years Experience</label>
                    <input type="number" min={0} className="form__input" style={{ width: "100%", marginTop: 6 }} value={yearsExperience} onChange={(e) => setYearsExperience(parseInt(e.target.value, 10) || 0)} />
                  </div>
                  <div>
                    <label className="form__label">Salary Min ($)</label>
                    <input type="number" step={5000} className="form__input" style={{ width: "100%", marginTop: 6 }} value={salaryMin ?? ""} onChange={(e) => setSalaryMin(e.target.value ? parseInt(e.target.value, 10) : null)} />
                  </div>
                  <div>
                    <label className="form__label">Salary Max ($)</label>
                    <input type="number" step={5000} className="form__input" style={{ width: "100%", marginTop: 6 }} value={salaryMax ?? ""} onChange={(e) => setSalaryMax(e.target.value ? parseInt(e.target.value, 10) : null)} />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, alignItems: "center" }}>
                  <div>
                    <label className="form__label">Location</label>
                    <input type="text" className="form__input" style={{ width: "100%", marginTop: 6 }} value={location} onChange={(e) => setLocation(e.target.value)} />
                  </div>
                  <div style={{ marginTop: 24 }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
                      <input type="checkbox" checked={remoteOk} onChange={(e) => setRemoteOk(e.target.checked)} style={{ width: 18, height: 18, accentColor: "var(--color-accent)" }} />
                      <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>Remote OK</span>
                    </label>
                  </div>
                </div>

                <button type="submit" disabled={saving} className="btn btn--primary" style={{ width: "100%", justifyContent: "center", marginTop: 12 }}>
                  {saving ? "Saving Changes…" : "Save Profile & Update Vector"}
                </button>

                <button type="button" onClick={handleResetSwipes} className="btn btn--outline" style={{ width: "100%", justifyContent: "center", marginTop: 12, borderColor: "var(--color-danger)", color: "var(--color-danger)" }}>
                  Reset Test Deck (Developer Tool)
                </button>
              </div>
            </form>
          </motion.div>
        )}

        {/* --- TAB CONTENT: MATCHES --- */}
        {activeTab === "matches" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
            {loadingMatches ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 16, width: "100%" }}>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="card" style={{ flexDirection: "row", alignItems: "center", padding: "20px 24px", animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}>
                    <div style={{ width: 60, height: 60, borderRadius: 16, background: "var(--color-border)" }} />
                    <div style={{ marginLeft: 20, display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
                      <div style={{ width: "40%", height: 16, background: "var(--color-border)", borderRadius: 4 }} />
                      <div style={{ width: "60%", height: 14, background: "var(--color-border)", borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : matches.length === 0 ? (
              <div className="empty-state" style={{ padding: "40px 0" }}>
                <h3 style={{ fontFamily: "var(--font-display)", fontWeight: 500, fontSize: "1.4rem", color: "var(--color-text)", marginBottom: 8 }}>
                  No matches yet
                </h3>
                <p>When you swipe right and clear the threshold,<br/>your applications will appear here.</p>
                <div style={{ marginTop: 20 }}>
                  <Link href="/feed" className="btn btn--primary">
                    Explore Job Deck →
                  </Link>
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 16, width: "100%" }}>
                {matches.map((m) => {
                  const scorePct = Math.round(m.score * 100);
                  const isExpanded = expandedId === m.id;
                  const breakdown = breakdowns[m.id];
                  
                  return (
                    <div key={m.id} className="card" style={{ padding: "20px 24px", transition: "all 0.3s ease" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                          <div style={{ width: 60, height: 60, borderRadius: 16, background: "var(--color-accent-subtle)", border: "1px solid rgba(193, 99, 61, 0.25)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                            <span style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--color-accent)" }}>
                              {scorePct}%
                            </span>
                            <span style={{ fontSize: "0.65rem", textTransform: "uppercase", color: "var(--color-accent-light)", fontWeight: 700 }}>
                              Match
                            </span>
                          </div>

                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                              <h3 style={{ fontSize: "1.1rem", fontFamily: "var(--font-display)", fontWeight: 700 }}>
                                {m.job_listing?.company_name || "Company"}
                              </h3>
                              {getStatusBadge(m.status)}
                            </div>
                            <p style={{ fontSize: "0.95rem", color: "var(--color-text)" }}>
                              {m.job_listing?.title || "Job Opportunity"}
                            </p>
                          </div>
                        </div>

                        <button className="btn btn--secondary btn--sm" onClick={() => toggleExpand(m.id)} style={{ minWidth: 100, justifyContent: "center" }}>
                          {isExpanded ? "Close" : "See Why ↓"}
                        </button>
                      </div>

                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }} style={{ overflow: "hidden" }}>
                            <div style={{ paddingTop: 24, marginTop: 24, borderTop: "1px solid var(--color-border)" }}>
                              {breakdown ? (
                                <MatchScoreBreakdown breakdown={breakdown} />
                              ) : (
                                <div style={{ textAlign: "center", color: "var(--color-text-muted)", padding: 20 }}>
                                  Loading breakdown...
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}

      </div>
    </main>
  );
}
