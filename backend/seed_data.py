import asyncio
import uuid
import sys

from sqlalchemy import select
from app.db.base import Base  # noqa: F401
import app.models.user  # noqa: F401
import app.models.company  # noqa: F401
import app.models.job_listing  # noqa: F401
import app.models.swipe  # noqa: F401
import app.models.match  # noqa: F401
import app.models.application  # noqa: F401

from app.db.session import AsyncSessionLocal
from app.models.company import Company, Recruiter
from app.models.job_listing import JobListing
from app.core.security import hash_password
from app.services.embedding_service import encode

# Helper to build a skill requirement dict
def req(skill: str) -> dict:
    return {"skill": skill, "level": "required"}

def pref(skill: str) -> dict:
    return {"skill": skill, "level": "preferred"}


SEED_COMPANIES = [
    # ── Developer Tools & Cloud ──────────────────────────────────────────────
    {
        "name": "Supastack Cloud",
        "industry": "Developer Tools & Cloud",
        "description": "Building next-generation cloud runtime and database primitives for modern web applications.",
        "recruiter_email": "recruiting@supastack.io",
        "jobs": [
            {
                "title": "Senior Full-Stack Engineer",
                "description": "Architect high-performance web applications, dashboard interfaces, and backend services. Experience with TypeScript, React, and async Python backends required.",
                "required_skills": [req("TypeScript"), req("React"), req("Python"), req("FastAPI"), req("PostgreSQL"), pref("Next.js"), pref("Docker")],
                "min_years_experience": 3,
                "salary_min": 140000, "salary_max": 185000,
                "location": "San Francisco, CA", "remote_ok": True, "seniority": "Senior",
            },
            {
                "title": "Staff Distributed Systems Engineer",
                "description": "Design ultra-low latency distributed coordination and storage engines handling millions of real-time queries.",
                "required_skills": [req("Go"), req("Distributed Systems"), req("PostgreSQL"), req("Docker"), pref("Redis"), pref("Kubernetes")],
                "min_years_experience": 5,
                "salary_min": 175000, "salary_max": 230000,
                "location": "Remote", "remote_ok": True, "seniority": "Staff",
            }
        ]
    },
    # ── Artificial Intelligence ──────────────────────────────────────────────
    {
        "name": "NeuralPath AI",
        "industry": "Artificial Intelligence",
        "description": "Enterprise AI search and retrieval platform using state-of-the-art dense embeddings and vector databases.",
        "recruiter_email": "talent@neuralpath.ai",
        "jobs": [
            {
                "title": "AI Platform Engineer",
                "description": "Scale dense retrieval pipelines, fine-tune transformer models, and optimize vector search indexing in PostgreSQL with pgvector.",
                "required_skills": [req("Python"), req("PyTorch"), req("PostgreSQL"), req("FastAPI"), pref("LLMs"), pref("pgvector"), pref("Docker")],
                "min_years_experience": 2,
                "salary_min": 150000, "salary_max": 200000,
                "location": "New York, NY", "remote_ok": True, "seniority": "Mid-Senior",
            },
            {
                "title": "Machine Learning Engineer",
                "description": "Design and train custom ranking and recommendation models. Work closely with product to ship personalized experiences.",
                "required_skills": [req("Python"), req("PyTorch"), req("SQL"), pref("Kafka"), pref("Kubernetes")],
                "min_years_experience": 2,
                "salary_min": 145000, "salary_max": 195000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Senior",
            }
        ]
    },
    # ── FinTech ──────────────────────────────────────────────────────────────
    {
        "name": "FinPulse Global",
        "industry": "FinTech",
        "description": "Modern API-first financial infrastructure powering real-time cross-border settlements and credit scoring.",
        "recruiter_email": "careers@finpulse.com",
        "jobs": [
            {
                "title": "Senior Backend Architect",
                "description": "Lead the core ledger and transactional payment execution engines. Strict adherence to idempotency, fault tolerance, and data integrity.",
                "required_skills": [req("Python"), req("FastAPI"), req("PostgreSQL"), req("Redis"), pref("Celery"), pref("Kafka"), pref("Docker")],
                "min_years_experience": 4,
                "salary_min": 160000, "salary_max": 210000,
                "location": "New York, NY", "remote_ok": True, "seniority": "Senior",
            },
            {
                "title": "Frontend Engineer (Design Systems)",
                "description": "Craft stunning, fluid banking interfaces and interactive analytics visualizations for institutional clients.",
                "required_skills": [req("React"), req("TypeScript"), req("Next.js"), pref("Tailwind CSS"), pref("Framer Motion")],
                "min_years_experience": 2,
                "salary_min": 125000, "salary_max": 165000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
    # ── HealthTech ───────────────────────────────────────────────────────────
    {
        "name": "Veloce Health",
        "industry": "HealthTech",
        "description": "Empowering doctors and researchers with AI-augmented clinical trial matching and patient diagnostics.",
        "recruiter_email": "jobs@velocehealth.org",
        "jobs": [
            {
                "title": "Full-Stack Software Engineer",
                "description": "Develop HIPAA-compliant patient onboarding flows, clinician dashboards, and medical record search tools.",
                "required_skills": [req("TypeScript"), req("React"), req("PostgreSQL"), pref("Node.js"), pref("Docker")],
                "min_years_experience": 2,
                "salary_min": 130000, "salary_max": 170000,
                "location": "Boston, MA", "remote_ok": True, "seniority": "Mid-Senior",
            }
        ]
    },
    # ── Cybersecurity & Infra ─────────────────────────────────────────────────
    {
        "name": "HyperScale Networks",
        "industry": "Cybersecurity & Infra",
        "description": "Zero-trust network access and edge computing platform protecting millions of connected devices.",
        "recruiter_email": "recruiting@hyperscale.io",
        "jobs": [
            {
                "title": "DevOps & Infrastructure Engineer",
                "description": "Manage multi-region Kubernetes clusters, automated GitOps deployment pipelines, and observability telemetry.",
                "required_skills": [req("Kubernetes"), req("Docker"), req("AWS"), req("Python"), pref("Terraform"), pref("CI/CD"), pref("Linux")],
                "min_years_experience": 3,
                "salary_min": 145000, "salary_max": 190000,
                "location": "Seattle, WA", "remote_ok": True, "seniority": "Senior",
            }
        ]
    },
    # ── Robotics ─────────────────────────────────────────────────────────────
    {
        "name": "Prism Robotics",
        "industry": "Robotics & Hardware",
        "description": "Autonomous warehouse robotics and computer vision systems optimizing global supply chains.",
        "recruiter_email": "team@prismrobotics.tech",
        "jobs": [
            {
                "title": "Computer Vision & ML Engineer",
                "description": "Deploy real-time object detection models and spatial tracking systems on edge devices.",
                "required_skills": [req("Python"), req("PyTorch"), req("OpenCV"), req("Deep Learning"), pref("Linux"), pref("C++")],
                "min_years_experience": 3,
                "salary_min": 155000, "salary_max": 205000,
                "location": "Austin, TX", "remote_ok": False, "seniority": "Senior",
            }
        ]
    },
    # ── E-Commerce ────────────────────────────────────────────────────────────
    {
        "name": "Aether Commerce",
        "industry": "E-Commerce & Retail",
        "description": "Headless commerce platform providing ultra-fast shopping experiences and modular inventory orchestration.",
        "recruiter_email": "people@aethercommerce.com",
        "jobs": [
            {
                "title": "Principal Web Performance Engineer",
                "description": "Drive core web vitals and sub-second page loads across thousands of global merchant storefronts.",
                "required_skills": [req("Next.js"), req("React"), req("TypeScript"), pref("HTML5"), pref("CSS3"), pref("GraphQL")],
                "min_years_experience": 5,
                "salary_min": 170000, "salary_max": 220000,
                "location": "Remote", "remote_ok": True, "seniority": "Principal",
            }
        ]
    },
    # ── Data & Analytics ─────────────────────────────────────────────────────
    {
        "name": "Chronos Analytics",
        "industry": "Data & Analytics",
        "description": "Time-series database and streaming analytics platform processing billions of telemetry events per second.",
        "recruiter_email": "jobs@chronosdata.com",
        "jobs": [
            {
                "title": "Lead Data Platform Engineer",
                "description": "Architect high-throughput real-time stream processing pipelines and automated analytical queries.",
                "required_skills": [req("Python"), req("PostgreSQL"), req("Docker"), pref("Kafka"), pref("Redis"), pref("REST API")],
                "min_years_experience": 4,
                "salary_min": 160000, "salary_max": 210000,
                "location": "Chicago, IL", "remote_ok": True, "seniority": "Lead",
            }
        ]
    },
    # ── Gaming ────────────────────────────────────────────────────────────────
    {
        "name": "OpenForge Studio",
        "industry": "Gaming & Web3",
        "description": "Creator studio and multiplayer game platform pioneering real-time procedural world generation.",
        "recruiter_email": "careers@openforge.gg",
        "jobs": [
            {
                "title": "Multiplayer Gameplay Engineer",
                "description": "Implement networked multiplayer synchronization, state serialization, and server authoritative simulations.",
                "required_skills": [req("Python"), req("Docker"), pref("C++"), pref("Go"), pref("Git"), pref("REST API")],
                "min_years_experience": 3,
                "salary_min": 135000, "salary_max": 180000,
                "location": "Los Angeles, CA", "remote_ok": True, "seniority": "Senior",
            }
        ]
    },
    # ── Security ─────────────────────────────────────────────────────────────
    {
        "name": "Beacon Security",
        "industry": "Cybersecurity",
        "description": "Automated vulnerability scanning and compliance management for high-growth SaaS companies.",
        "recruiter_email": "security@beaconsec.io",
        "jobs": [
            {
                "title": "Application Security Engineer",
                "description": "Perform penetration testing, static code analysis, and design security guardrails across cloud applications.",
                "required_skills": [req("Python"), req("Linux"), req("Docker"), pref("AWS"), pref("REST API"), pref("Git")],
                "min_years_experience": 3,
                "salary_min": 145000, "salary_max": 195000,
                "location": "Remote", "remote_ok": True, "seniority": "Senior",
            }
        ]
    },
    # ── Creative Tools ────────────────────────────────────────────────────────
    {
        "name": "Lumina Creative",
        "industry": "Creative Tools",
        "description": "Next-generation collaborative canvas and 3D modeling tool running directly in WebGPU in the browser.",
        "recruiter_email": "hello@luminacreative.design",
        "jobs": [
            {
                "title": "Frontend Graphics Engineer",
                "description": "Build high-performance graphics pipelines, scene graphs, and vector manipulation UI in the browser.",
                "required_skills": [req("TypeScript"), req("React"), req("JavaScript"), pref("HTML5"), pref("CSS3"), pref("Framer Motion")],
                "min_years_experience": 3,
                "salary_min": 140000, "salary_max": 190000,
                "location": "San Francisco, CA", "remote_ok": True, "seniority": "Senior",
            }
        ]
    },
    # ── Supply Chain ──────────────────────────────────────────────────────────
    {
        "name": "Kite Logistics",
        "industry": "Supply Chain & Logistics",
        "description": "Smart freight dispatching and carbon-neutral route optimization network.",
        "recruiter_email": "dispatch@kitelogistics.com",
        "jobs": [
            {
                "title": "Operations Systems Engineer",
                "description": "Build algorithmic load-matching engines and dispatch dashboards connecting carriers with shippers.",
                "required_skills": [req("Python"), req("FastAPI"), req("PostgreSQL"), pref("Celery"), pref("Redis"), pref("TypeScript")],
                "min_years_experience": 2,
                "salary_min": 125000, "salary_max": 165000,
                "location": "Atlanta, GA", "remote_ok": True, "seniority": "Mid-Senior",
            }
        ]
    },
    # ── FinTech (Go) ──────────────────────────────────────────────────────────
    {
        "name": "Golang Gateway",
        "industry": "FinTech",
        "description": "High frequency trading systems and low latency microservices.",
        "recruiter_email": "recruiting@golanggateway.com",
        "jobs": [
            {
                "title": "Backend Engineer (Go)",
                "description": "Develop core services for our trading platform using Go microservices.",
                "required_skills": [req("Go"), req("PostgreSQL"), pref("Docker"), pref("Redis")],
                "min_years_experience": 1,
                "salary_min": 110000, "salary_max": 150000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
    # ── Enterprise Software ────────────────────────────────────────────────────
    {
        "name": "C-Sharp Innovations",
        "industry": "Enterprise Software",
        "description": "Building the next generation of enterprise management tools using the .NET ecosystem.",
        "recruiter_email": "jobs@csharpinnovations.com",
        "jobs": [
            {
                "title": ".NET Developer",
                "description": "Build scalable APIs and services using C# and .NET Core for enterprise clients.",
                "required_skills": [req("C#"), req(".NET Core"), pref("SQL Server"), pref("Azure")],
                "min_years_experience": 2,
                "salary_min": 100000, "salary_max": 140000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
    # ── SaaS / Productivity ────────────────────────────────────────────────────
    {
        "name": "Flowdesk",
        "industry": "SaaS & Productivity",
        "description": "All-in-one project management and async collaboration platform for remote-first engineering teams.",
        "recruiter_email": "engineering@flowdesk.app",
        "jobs": [
            {
                "title": "Full-Stack Product Engineer",
                "description": "Own end-to-end features from database to UI. Work across our React frontend, Python API, and PostgreSQL data layer.",
                "required_skills": [req("Python"), req("React"), req("TypeScript"), req("PostgreSQL"), pref("FastAPI"), pref("Docker")],
                "min_years_experience": 2,
                "salary_min": 130000, "salary_max": 175000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Senior",
            },
            {
                "title": "Backend Engineer (Integrations)",
                "description": "Build webhook ingestion pipelines and third-party integration connectors. Obsess over reliability and idempotency.",
                "required_skills": [req("Python"), req("FastAPI"), req("PostgreSQL"), pref("Redis"), pref("Celery")],
                "min_years_experience": 2,
                "salary_min": 125000, "salary_max": 165000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
    # ── EdTech ────────────────────────────────────────────────────────────────
    {
        "name": "SkillBridge Academy",
        "industry": "EdTech",
        "description": "Adaptive learning platform helping engineers upskill through AI-driven personalized curriculum.",
        "recruiter_email": "team@skillbridge.io",
        "jobs": [
            {
                "title": "Platform Engineer",
                "description": "Build the infrastructure powering 500k+ active learners. Own our content delivery, progress tracking, and recommendation systems.",
                "required_skills": [req("Python"), req("PostgreSQL"), req("Docker"), pref("React"), pref("TypeScript"), pref("AWS")],
                "min_years_experience": 2,
                "salary_min": 120000, "salary_max": 160000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
    # ── ClimateTech ────────────────────────────────────────────────────────────
    {
        "name": "CarbonGrid",
        "industry": "ClimateTech",
        "description": "Real-time energy grid optimization and carbon market analytics platform.",
        "recruiter_email": "hire@carbongrid.earth",
        "jobs": [
            {
                "title": "Data Infrastructure Engineer",
                "description": "Build pipelines that ingest billions of IoT sensor readings per day and power our carbon accounting dashboards.",
                "required_skills": [req("Python"), req("PostgreSQL"), req("Docker"), pref("Kafka"), pref("REST API")],
                "min_years_experience": 2,
                "salary_min": 125000, "salary_max": 165000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
    # ── Media & Streaming ─────────────────────────────────────────────────────
    {
        "name": "WaveStream",
        "industry": "Media & Entertainment",
        "description": "Next-generation live and on-demand streaming platform with AI-powered content recommendations.",
        "recruiter_email": "engineering@wavestream.tv",
        "jobs": [
            {
                "title": "Streaming Backend Engineer",
                "description": "Build the scalable video ingest, transcoding, and adaptive bitrate delivery systems powering millions of streams.",
                "required_skills": [req("Python"), req("FastAPI"), req("PostgreSQL"), req("Docker"), pref("Redis"), pref("AWS")],
                "min_years_experience": 3,
                "salary_min": 140000, "salary_max": 185000,
                "location": "Los Angeles, CA", "remote_ok": True, "seniority": "Senior",
            },
            {
                "title": "React Frontend Engineer",
                "description": "Build our beautiful, performant web player and creator dashboard used by millions of viewers worldwide.",
                "required_skills": [req("React"), req("TypeScript"), req("JavaScript"), pref("Next.js"), pref("CSS3")],
                "min_years_experience": 2,
                "salary_min": 120000, "salary_max": 160000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
    # ── Developer Tooling ─────────────────────────────────────────────────────
    {
        "name": "CodeLens",
        "industry": "Developer Tools",
        "description": "Intelligent code review and static analysis platform that integrates directly into your CI pipeline.",
        "recruiter_email": "jobs@codelens.dev",
        "jobs": [
            {
                "title": "Backend Engineer (Analysis Engine)",
                "description": "Build the AST parsing and semantic analysis engines that power our code review automation.",
                "required_skills": [req("Python"), req("PostgreSQL"), req("Docker"), pref("FastAPI"), pref("REST API"), pref("CI/CD")],
                "min_years_experience": 2,
                "salary_min": 130000, "salary_max": 170000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Senior",
            }
        ]
    },
    # ── Marketplace ───────────────────────────────────────────────────────────
    {
        "name": "Depot Marketplace",
        "industry": "Marketplace & B2B",
        "description": "B2B procurement marketplace connecting buyers and suppliers across the manufacturing sector.",
        "recruiter_email": "engineering@depotmarket.com",
        "jobs": [
            {
                "title": "Fullstack Engineer",
                "description": "Build the buyer-facing catalog, supplier portals, and order management flows for our core marketplace.",
                "required_skills": [req("Python"), req("React"), req("TypeScript"), req("PostgreSQL"), pref("FastAPI"), pref("Next.js")],
                "min_years_experience": 2,
                "salary_min": 120000, "salary_max": 160000,
                "location": "Remote", "remote_ok": True, "seniority": "Mid-Level",
            }
        ]
    },
]


async def seed():
    print("Starting company and job listing seed process...")
    async with AsyncSessionLocal() as session:
        # Check existing companies
        existing_res = await session.execute(select(Company))
        existing_companies = existing_res.scalars().all()
        existing_names = {c.name for c in existing_companies}

        # Check existing recruiter emails to avoid unique constraint violations
        existing_recruiter_res = await session.execute(select(Recruiter))
        existing_recruiter_emails = {r.email for r in existing_recruiter_res.scalars().all()}

        total_companies_created = 0
        total_jobs_created = 0

        for comp_data in SEED_COMPANIES:
            if comp_data["name"] in existing_names:
                print(f"Skipping already seeded company: {comp_data['name']}")
                continue

            tenant_id = uuid.uuid4()
            company = Company(
                name=comp_data["name"],
                industry=comp_data["industry"],
                description=comp_data["description"],
                tenant_id=tenant_id,
            )
            session.add(company)
            await session.flush()

            # Add Recruiter (skip if email already exists)
            if comp_data["recruiter_email"] not in existing_recruiter_emails:
                recruiter = Recruiter(
                    company_id=company.id,
                    email=comp_data["recruiter_email"],
                    hashed_password=hash_password("Password123!"),
                    role="owner",
                )
                session.add(recruiter)
                await session.flush()
                existing_recruiter_emails.add(comp_data["recruiter_email"])
            else:
                print(f"Skipping duplicate recruiter email: {comp_data['recruiter_email']}")

            # Add Jobs
            for job_info in comp_data["jobs"]:
                # Build embedding text from skill names only
                skill_names = " ".join(
                    s["skill"] if isinstance(s, dict) else s
                    for s in job_info["required_skills"]
                )
                text = f"{job_info['title']} {job_info['description']} {skill_names}"
                try:
                    embedding = encode(text.strip())
                except Exception as e:
                    print(f"Embedding generation fallback for {job_info['title']}: {e}")
                    embedding = None

                job = JobListing(
                    company_id=company.id,
                    tenant_id=tenant_id,
                    title=job_info["title"],
                    description=job_info["description"],
                    required_skills=job_info["required_skills"],
                    min_years_experience=job_info["min_years_experience"],
                    salary_min=job_info["salary_min"],
                    salary_max=job_info["salary_max"],
                    location=job_info["location"],
                    remote_ok=job_info["remote_ok"],
                    seniority=job_info["seniority"],
                    listing_embedding=embedding,
                    is_active=True,
                )
                session.add(job)
                total_jobs_created += 1

            total_companies_created += 1

        await session.commit()
        print(f"\n[SUCCESS] Seeded {total_companies_created} companies and {total_jobs_created} jobs!")
        print("Candidate feed is now fully stocked and ready to swipe.")


if __name__ == "__main__":
    asyncio.run(seed())
