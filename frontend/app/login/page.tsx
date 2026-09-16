"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { motion } from "framer-motion";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const role = await login(email, password);
      if (role === "candidate") {
        router.push("/feed");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please check your email and password.");
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
          <div className="auth-icon">Job<span style={{ color: "var(--color-text)" }}>score</span></div>
          <h1>Welcome back</h1>
          <p>Sign in to access your Jobscore account</p>
        </div>

        <div className="auth-card">
          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="form" style={{ maxWidth: "100%" }}>
            <div>
              <label className="form__label">Email address</label>
              <input
                type="email"
                required
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <label className="form__label">Password</label>
              <input
                type="password"
                required
                className="form__input"
                style={{ width: "100%", marginTop: 6 }}
                placeholder="••••••••"
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
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Don&apos;t have an account?{" "}
              <Link href="/register/candidate" style={{ fontWeight: 600 }}>
                Sign up as Candidate
              </Link>
            </p>
            <p style={{ marginTop: 6 }}>
              Hiring talent?{" "}
              <Link href="/register/company" style={{ fontWeight: 600 }}>
                Register Company
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
