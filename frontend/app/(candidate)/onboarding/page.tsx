"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";

export default function OnboardingPage() {
  const router = useRouter();
  const { refreshCandidateProfile } = useAuth();

  // Form state - no fake defaults!
  const [summary, setSummary] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [yearsExperience, setYearsExperience] = useState<number | "">("");
  const [salaryMin, setSalaryMin] = useState<number | "">("");
  const [salaryMax, setSalaryMax] = useState<number | "">("");
  const [location, setLocation] = useState("");
  const [remoteOk, setRemoteOk] = useState(false);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addSkill() {
    // Split on commas so pasting "React, TypeScript, Next.js" adds each separately
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
    if (skills.length === 0) {
      setError("Please add at least one technical skill.");
      return;
    }
    if (salaryMin !== "" && salaryMax !== "" && salaryMin > salaryMax) {
      setError("Minimum salary cannot be greater than maximum salary.");
      return;
    }
    if (!location && !remoteOk) {
      setError("Please specify a location or check 'Open to Remote'.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await apiClient.updateCandidateProfile({
        resume_summary: summary,
        skills,
        years_experience: yearsExperience === "" ? 0 : yearsExperience,
        desired_salary_min: salaryMin === "" ? null : salaryMin,
        desired_salary_max: salaryMax === "" ? null : salaryMax,
        location,
        remote_ok: remoteOk,
      });

      await refreshCandidateProfile();
      router.refresh(); // bust the feed cache so it re-ranks with the new profile
      router.push("/feed");
    } catch (err: any) {
      setError(err.message || "Failed to save profile. Please try again.");
      setSaving(false);
    }
  }

  return (
    <main className="page">
      <div style={{ maxWidth: 720, width: "100%", margin: "0 auto" }}>
        {/* Progress header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <span className="badge badge--primary" style={{ marginBottom: 12 }}>
            Step 2 of 2 · Onboarding
          </span>
          <h1>Match Preferences</h1>
          <p>
            Tell us about your skills and experience. We'll generate your match vector so you
            only see roles that genuinely fit.
          </p>
        </div>

        {error && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.12)",
              border: "1px solid var(--color-danger)",
              color: "var(--color-danger)",
              padding: "12px 16px",
              borderRadius: 12,
              fontSize: "0.9rem",
              marginBottom: 24,
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div
            style={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-card)",
              padding: 28,
              boxShadow: "var(--shadow-card)",
              display: "flex",
              flexDirection: "column",
              gap: 20,
            }}
          >
            <h3 style={{ borderBottom: "1px solid var(--color-border)", paddingBottom: 12 }}>
              Your Background
            </h3>

            {/* Resume Summary */}
            <div>
              <label className="form__label">Professional Summary</label>
              <textarea
                className="form__input"
                rows={3}
                style={{ width: "100%", marginTop: 6, resize: "vertical" }}
                placeholder="Brief summary of your background, specialties, and engineering impact…"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                required
                minLength={20}
              />
              <span style={{ fontSize: "0.75rem", color: "var(--color-text-dim)", marginTop: 4, display: "block" }}>
                This is embedded semantically to match with job listing embeddings.
              </span>
            </div>

            {/* Skills Tag Cloud */}
            <div>
              <label className="form__label">Technical Skills</label>
              <div style={{ marginTop: 8, marginBottom: 12 }}>
                <div className="skill-chips">
                  {skills.map((skill) => (
                    <span key={skill} className="skill-chip skill-chip--highlight">
                      {skill}
                      <button
                        type="button"
                        onClick={() => removeSkill(skill)}
                        className="skill-chip__remove"
                        aria-label={`Remove ${skill}`}
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="skill-input-container">
                <input
                  type="text"
                  className="form__input"
                  style={{ flex: 1 }}
                  placeholder="e.g. React, TypeScript, Python — press Enter or comma"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === ",") {
                      e.preventDefault();
                      addSkill();
                    }
                  }}
                />
                <button type="button" onClick={addSkill} className="btn btn--secondary btn--sm">
                  + Add
                </button>
              </div>
            </div>

            {/* Experience & Salary Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              <div>
                <label className="form__label">Years of Experience</label>
                <input
                  type="number"
                  min={0}
                  max={40}
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  value={yearsExperience}
                  onChange={(e) => setYearsExperience(e.target.value === "" ? "" : parseInt(e.target.value, 10))}
                  required
                />
              </div>

              <div>
                <label className="form__label">Desired Salary Min ($)</label>
                <input
                  type="number"
                  step={5000}
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  value={salaryMin}
                  onChange={(e) => setSalaryMin(e.target.value === "" ? "" : parseInt(e.target.value, 10))}
                  placeholder="e.g. 120000"
                />
              </div>

              <div>
                <label className="form__label">Desired Salary Max ($)</label>
                <input
                  type="number"
                  step={5000}
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  value={salaryMax}
                  onChange={(e) => setSalaryMax(e.target.value === "" ? "" : parseInt(e.target.value, 10))}
                  placeholder="e.g. 160000"
                />
              </div>
            </div>

            {/* Location & Remote OK */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, alignItems: "center" }}>
              <div>
                <label className="form__label">Metro / Location</label>
                <input
                  type="text"
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  placeholder="e.g. San Francisco, CA or Remote"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
              </div>

              <div style={{ marginTop: 24 }}>
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    cursor: "pointer",
                    userSelect: "none",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={remoteOk}
                    onChange={(e) => setRemoteOk(e.target.checked)}
                    style={{ width: 18, height: 18, accentColor: "var(--color-accent)" }}
                  />
                  <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>Open to Remote</span>
                </label>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="btn btn--primary btn--lg"
            style={{ width: "100%", justifyContent: "center" }}
          >
            {saving ? "Generating Match Vector…" : "Complete Preferences & Start Swiping →"}
          </button>
        </form>
      </div>
    </main>
  );
}
