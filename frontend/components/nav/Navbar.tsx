"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export function Navbar() {
  const { user, candidateProfile, logout } = useAuth();
  const pathname = usePathname();

  return (
    <header className="navbar">
      <div className="navbar__container">
        <Link href="/" className="navbar__logo">
          <span className="navbar__logo-text">
            job<span className="navbar__logo-accent">score.</span>
          </span>
        </Link>

        <nav className="navbar__nav">
          {user?.role === "candidate" && (
            <>
              {/* Removed extra candidate links - relying on Logo and Profile */}
            </>
          )}

          {user?.role === "recruiter" && (
            <>
              <Link
                href="/dashboard"
                className={`navbar__link ${pathname === "/dashboard" ? "navbar__link--active" : ""}`}
              >
                Recruiting Funnel
              </Link>
              <Link
                href="/jobs"
                className={`navbar__link ${pathname.startsWith("/jobs") && pathname !== "/jobs/new" ? "navbar__link--active" : ""}`}
              >
                Active Roles
              </Link>
              <Link
                href="/jobs/new"
                className="navbar__btn-post"
              >
                + Post Job
              </Link>
            </>
          )}

          {!user && (
            <>
              <Link href="/register/candidate" className="navbar__link">
                For Candidates
              </Link>
              <Link href="/register/company" className="navbar__link">
                For Employers
              </Link>
            </>
          )}
        </nav>

        <div className="navbar__actions">
          {user ? (
            <div className="navbar__user-menu">
              <Link href={user.role === "candidate" ? "/profile" : "/dashboard"} className="btn btn--outline btn--sm">
                {user.role === "candidate" ? "My Profile" : "Dashboard"}
              </Link>
              <button onClick={logout} className="navbar__logout-btn" title="Sign out">
                Log out
              </button>
            </div>
          ) : (
            <div className="navbar__auth-buttons">
              <Link href="/login" className="btn btn--secondary btn--sm">
                Sign In
              </Link>
              <Link href="/register/candidate" className="btn btn--primary btn--sm">
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
