"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { motion } from "framer-motion";

export default function CandidateRegisterPage() {
  const router = useRouter();
  const { registerCandidate } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await registerCandidate({ name, email, password });
      router.push("/onboarding");
    } catch (err: any) {
      setError(err.message || "Failed to create candidate account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page" style={{ justifyContent: "center" }}>
      <motion.div 
        className="auth-wrapper"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
      >
        <div className="auth-header">
          <span className="badge badge--primary" style={{ marginBottom: 12 }}>
            Candidate Portal
          </span>
          <h1>Create your profile</h1>
          <p>Next-gen explainable matching. Tell us your skills & find your fit.</p>
        </div>

        <div className="auth-card">
          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="form" style={{ maxWidth: "100%" }}>
            <div>
              <label className="form__label">Full name</label>
              <input
                type="text"
                required
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="Alex Mercer"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div>
              <label className="form__label">Email address</label>
              <input
                type="email"
                required
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="alex@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn--primary"
              style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            >
              {loading ? "Creating Account…" : "Continue to Match Preferences →"}
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
              Looking to hire candidates?{" "}
              <Link href="/register/company" style={{ fontWeight: 600 }}>
                Register as an Employer
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
