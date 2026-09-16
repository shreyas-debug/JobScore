"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { motion } from "framer-motion";

export default function CompanyRegisterPage() {
  const router = useRouter();
  const { registerCompany } = useAuth();
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [description, setDescription] = useState("");
  const [recruiterEmail, setRecruiterEmail] = useState("");
  const [recruiterPassword, setRecruiterPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await registerCompany({
        company_name: companyName,
        industry: industry || undefined,
        description: description || undefined,
        recruiter_email: recruiterEmail,
        recruiter_password: recruiterPassword,
      });
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to register company.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page" style={{ justifyContent: "center" }}>
      <motion.div 
        className="auth-wrapper"
        style={{ maxWidth: 480 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
      >
        <div className="auth-header">
          <span className="badge badge--success" style={{ marginBottom: 12 }}>
            Employer Portal
          </span>
          <h1>Post once. Receive matches.</h1>
          <p>Only review high-relevance candidates who cleared the match threshold.</p>
        </div>

        <div className="auth-card">
          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="form" style={{ maxWidth: "100%" }}>
            <div>
              <label className="form__label">Company Name</label>
              <input
                type="text"
                required
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="Acme Technologies"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>

            <div>
              <label className="form__label">Industry</label>
              <input
                type="text"
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="e.g. Fintech, AI, HealthTech"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
              />
            </div>

            <div>
              <label className="form__label">Company Description</label>
              <textarea
                className="form__input"
                rows={2}
                style={{ width: "100%", marginTop: 6, resize: "vertical" }}
                placeholder="Short blurb about what your company builds…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div>
              <label className="form__label">Recruiter / Admin Email</label>
              <input
                type="email"
                required
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="recruiter@acme.com"
                value={recruiterEmail}
                onChange={(e) => setRecruiterEmail(e.target.value)}
              />
            </div>

            <div>
              <label className="form__label">Password</label>
              <input
                type="password"
                required
                minLength={8}
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="Minimum 8 characters"
                value={recruiterPassword}
                onChange={(e) => setRecruiterPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn--primary"
              style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            >
              {loading ? "Registering Company…" : "Create Company Account →"}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Already have an account?{" "}
              <Link href="/login" style={{ fontWeight: 600 }}>
                Sign In
              </Link>
            </p>
            <p style={{ marginTop: 6 }}>
              Looking for a job?{" "}
              <Link href="/register/candidate" style={{ fontWeight: 600 }}>
                Register as Candidate
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
