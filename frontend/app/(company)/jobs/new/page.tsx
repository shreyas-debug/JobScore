"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import type { SkillRequirement } from "@/lib/types";

export default function NewJobPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [skills, setSkills] = useState<SkillRequirement[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [minYearsExp, setMinYearsExp] = useState<number | "">("");
  const [salaryMin, setSalaryMin] = useState<number | "">("");
  const [salaryMax, setSalaryMax] = useState<number | "">("");
  const [location, setLocation] = useState("");
  const [remoteOk, setRemoteOk] = useState(false);
  const [seniority, setSeniority] = useState("");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addSkill() {
    const trimmed = newSkill.trim();
    if (trimmed && !skills.find(s => s.skill === trimmed)) {
      setSkills([...skills, { skill: trimmed, level: "required" }]);
      setNewSkill("");
    }
  }

  function removeSkill(skill: string) {
    setSkills(skills.filter((s) => s.skill !== skill));
  }

  function toggleLevel(skill: string) {
    setSkills(skills.map(s => 
      s.skill === skill
        ? { ...s, level: s.level === "required" ? "preferred" : "required" }
        : s
    ));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (skills.length === 0) {
      setError("Please add at least one required skill.");
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
      await apiClient.createJob({
        title,
        description,
        required_skills: skills,
        min_years_experience: minYearsExp === "" ? 0 : minYearsExp,
        salary_min: salaryMin === "" ? null : salaryMin,
        salary_max: salaryMax === "" ? null : salaryMax,
        location,
        remote_ok: remoteOk,
        seniority,
      });

      router.push("/jobs");
    } catch (err: any) {
      setError(err.message || "Failed to create job listing.");
      setSaving(false);
    }
  }

  return (
    <main className="page">
      <div style={{ maxWidth: 680, width: "100%", margin: "0 auto" }}>
        <div style={{ marginBottom: 24 }}>
          <Link href="/jobs" style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
            ← Back to All Roles
          </Link>
          <h1 style={{ marginTop: 8 }}>Post a New Role</h1>
          <p>
            When candidates swipe right on this listing, our two-stage engine scores them against your
            semantic vector and requirements automatically.
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
              marginBottom: 20,
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div
            style={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-card)",
              padding: 32,
              boxShadow: "var(--shadow-card)",
              display: "flex",
              flexDirection: "column",
              gap: 20,
            }}
          >
            <div>
              <label className="form__label">Role Title</label>
              <input
                type="text"
                required
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="e.g. Senior Full-Stack Engineer"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div>
              <label className="form__label">Job Description & Responsibilities</label>
              <textarea
                required
                className="form__input"
                rows={4}
                style={{ width: "100%", marginTop: 6, resize: "vertical" }}
                placeholder="Describe the challenges, tech stack, and impact of this role…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            {/* Skills */}
            <div>
              <label className="form__label">Skills</label>
              <p style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", margin: "4px 0 10px" }}>
                Add skills and toggle between <strong>Required</strong> (solid) and <strong>Preferred</strong> (dashed) — required skills count more in matching.
              </p>
              <div style={{ marginTop: 8, marginBottom: 12 }}>
                <div className="skill-chips">
                  {skills.map((s) => (
                    <span
                      key={s.skill}
                      className="skill-chip skill-chip--highlight"
                      style={s.level === "preferred" ? {
                        borderStyle: "dashed",
                        background: "transparent",
                        color: "var(--color-text-muted)"
                      } : {}}
                    >
                      <button
                        type="button"
                        onClick={() => toggleLevel(s.skill)}
                        title={`Currently ${s.level} — click to toggle`}
                        style={{ background: "none", border: "none", cursor: "pointer", fontSize: "0.7rem", fontWeight: 700, color: s.level === "required" ? "var(--color-accent)" : "var(--color-text-dim)", padding: "0 4px 0 0" }}
                      >
                        {s.level === "required" ? "REQ" : "PREF"}
                      </button>
                      {s.skill}
                      <button
                        type="button"
                        onClick={() => removeSkill(s.skill)}
                        className="skill-chip__remove"
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
                  placeholder="e.g. PostgreSQL, Next.js, Docker"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
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

            {/* Exp & Seniority */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label className="form__label">Minimum Years Experience</label>
                <input
                  type="number"
                  min={0}
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  value={minYearsExp}
                  onChange={(e) => setMinYearsExp(e.target.value === "" ? "" : parseInt(e.target.value, 10))}
                  required
                />
              </div>

              <div>
                <label className="form__label">Seniority Level</label>
                <input
                  type="text"
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  placeholder="e.g. Senior, Lead, Staff"
                  value={seniority}
                  onChange={(e) => setSeniority(e.target.value)}
                />
              </div>
            </div>

            {/* Salary Range */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label className="form__label">Salary Min ($ USD)</label>
                <input
                  type="number"
                  step={5000}
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  value={salaryMin}
                  onChange={(e) => setSalaryMin(e.target.value === "" ? "" : parseInt(e.target.value, 10))}
                  placeholder="e.g. 130000"
                />
              </div>

              <div>
                <label className="form__label">Salary Max ($ USD)</label>
                <input
                  type="number"
                  step={5000}
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  value={salaryMax}
                  onChange={(e) => setSalaryMax(e.target.value === "" ? "" : parseInt(e.target.value, 10))}
                  placeholder="e.g. 170000"
                />
              </div>
            </div>

            {/* Location & Remote */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, alignItems: "center" }}>
              <div>
                <label className="form__label">Location / Metro</label>
                <input
                  type="text"
                  className="form__input"
                  style={{ width: "100%", marginTop: 6 }}
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
              </div>

              <div style={{ marginTop: 24 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={remoteOk}
                    onChange={(e) => setRemoteOk(e.target.checked)}
                    style={{ width: 18, height: 18, accentColor: "var(--color-accent)" }}
                  />
                  <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>Remote OK</span>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="btn btn--primary btn--lg"
              style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            >
              {saving ? "Publishing & Vectorizing…" : "Publish Job Listing →"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
