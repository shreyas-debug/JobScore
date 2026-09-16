"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";

const ROLES = [
  "Frontend Engineer",
  "Backend Engineer",
  "ML Engineer",
  "Design Lead",
  "DevOps Engineer",
];

export default function Home() {
  const [roleIdx, setRoleIdx] = useState(0);
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) {
      if (user.role === "candidate") {
        router.push("/feed");
      } else if (user.role === "recruiter") {
        router.push("/dashboard");
      }
    }
  }, [user, router]);

  useEffect(() => {
    const interval = setInterval(() => {
      setRoleIdx((i) => (i + 1) % ROLES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  if (user) {
    return null; // prevent flash of homepage content before redirect
  }

  return (
    <main style={{
      height: "calc(100vh - 68px)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      overflow: "hidden"
    }}>
      <div style={{
        maxWidth: 800,
        width: "100%",
        padding: "0 24px",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 32
      }}>
        <div className="hero__eyebrow" style={{ marginBottom: 16 }}>
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "var(--color-accent)",
              flexShrink: 0,
            }}
          />
          Relevance-First Matchmaking
        </div>

        <h1 className="hero__title" style={{ fontSize: "clamp(2.5rem, 6vw, 4.2rem)", margin: 0 }}>
          Find roles that actually{" "}
          <span className="hero__title-accent">fit you.</span>
          <br />
          <div style={{ height: "1.2em", position: "relative", overflow: "hidden", marginTop: 8 }}>
            <AnimatePresence mode="wait">
              <motion.span
                key={roleIdx}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -20, opacity: 0 }}
                transition={{ duration: 0.3 }}
                style={{
                  display: "block",
                  color: "var(--color-text-muted)",
                  fontSize: "clamp(1.5rem, 4vw, 2.4rem)",
                  fontWeight: 600,
                  letterSpacing: "-0.02em"
                }}
              >
                {ROLES[roleIdx]}
              </motion.span>
            </AnimatePresence>
          </div>
        </h1>

        <p className="hero__desc" style={{ maxWidth: 540, margin: "0 auto", fontSize: "1.1rem" }}>
          Stop sending blind applications into a void. Jobscore surfaces roles where you genuinely clear the bar, with transparent score breakdowns.
        </p>

        <div className="hero__ctas" style={{ marginTop: 16 }}>
          <Link href="/register/candidate" className="btn btn--primary btn--lg">
            Find My Match →
          </Link>
          <Link href="/register/company" className="btn btn--secondary btn--lg">
            I&apos;m Hiring
          </Link>
        </div>
      </div>
    </main>
  );
}
