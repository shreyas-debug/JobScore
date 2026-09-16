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

SEED_COMPANIES = [
    {
        "name": "Supastack Cloud",
        "industry": "Developer Tools & Cloud",
        "description": "Building next-generation cloud runtime and database primitives for modern web applications.",
        "recruiter_email": "recruiting@supastack.io",
        "jobs": [
            {
                "title": "Senior Full-Stack Engineer",
                "description": "Architect high-performance web applications, dashboard interfaces, and backend services. Experience with TypeScript, React, and async Python backends required.",
                "required_skills": ["TypeScript", "React", "Next.js", "Python", "FastAPI", "PostgreSQL"],
                "min_years_experience": 3,
                "salary_min": 140000,
                "salary_max": 185000,
                "location": "San Francisco, CA",
                "remote_ok": True,
                "seniority": "Senior",
            },
            {
                "title": "Staff Distributed Systems Engineer",
                "description": "Design ultra-low latency distributed coordination and storage engines handling millions of real-time queries.",
                "required_skills": ["Go", "Distributed Systems", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
                "min_years_experience": 5,
                "salary_min": 175000,
                "salary_max": 230000,
                "location": "Remote",
                "remote_ok": True,
                "seniority": "Staff",
            }
        ]
    },
    {
        "name": "NeuralPath AI",
        "industry": "Artificial Intelligence",
        "description": "Enterprise AI search and retrieval platform using state-of-the-art dense embeddings and vector databases.",
        "recruiter_email": "talent@neuralpath.ai",
        "jobs": [
            {
                "title": "AI Platform Engineer",
                "description": "Scale dense retrieval pipelines, fine-tune transformer models, and optimize vector search indexing in PostgreSQL with pgvector.",
                "required_skills": ["Python", "PyTorch", "LLMs", "pgvector", "PostgreSQL", "Docker", "FastAPI"],
                "min_years_experience": 2,
                "salary_min": 150000,
                "salary_max": 200000,
                "location": "New York, NY",
                "remote_ok": True,
                "seniority": "Mid-Senior",
            }
        ]
    },
    {
        "name": "FinPulse Global",
        "industry": "FinTech",
        "description": "Modern API-first financial infrastructure powering real-time cross-border settlements and credit scoring.",
        "recruiter_email": "careers@finpulse.com",
        "jobs": [
            {
                "title": "Senior Backend Architect",
                "description": "Lead the core ledger and transactional payment execution engines. Strict adherence to idempotency, fault tolerance, and data integrity.",
                "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Celery", "Kafka", "Docker"],
                "min_years_experience": 4,
                "salary_min": 160000,
                "salary_max": 210000,
                "location": "New York, NY",
                "remote_ok": True,
                "seniority": "Senior",
            },
            {
                "title": "Frontend Engineer (Design Systems)",
                "description": "Craft stunning, fluid banking interfaces and interactive analytics visualizations for institutional clients.",
                "required_skills": ["React", "TypeScript", "Tailwind CSS", "Framer Motion", "Next.js"],
                "min_years_experience": 2,
                "salary_min": 125000,
                "salary_max": 165000,
                "location": "Remote",
                "remote_ok": True,
                "seniority": "Mid-Level",
            }
        ]
    },
    {
        "name": "Veloce Health",
        "industry": "HealthTech",
        "description": "Empowering doctors and researchers with AI-augmented clinical trial matching and patient diagnostics.",
        "recruiter_email": "jobs@velocehealth.org",
        "jobs": [
            {
                "title": "Full-Stack Software Engineer",
                "description": "Develop HIPAA-compliant patient onboarding flows, clinician dashboards, and medical record search tools.",
                "required_skills": ["TypeScript", "React", "Node.js", "PostgreSQL", "Docker"],
                "min_years_experience": 2,
                "salary_min": 130000,
                "salary_max": 170000,
                "location": "Boston, MA",
                "remote_ok": True,
                "seniority": "Mid-Senior",
            }
        ]
    },
    {
        "name": "HyperScale Networks",
        "industry": "Cybersecurity & Infra",
        "description": "Zero-trust network access and edge computing platform protecting millions of connected devices.",
        "recruiter_email": "recruiting@hyperscale.io",
        "jobs": [
            {
                "title": "DevOps & Infrastructure Engineer",
                "description": "Manage multi-region Kubernetes clusters, automated GitOps deployment pipelines, and observability telemetry with Prometheus and Grafana.",
                "required_skills": ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "Linux", "Python"],
                "min_years_experience": 3,
                "salary_min": 145000,
                "salary_max": 190000,
                "location": "Seattle, WA",
                "remote_ok": True,
                "seniority": "Senior",
            }
        ]
    },
    {
        "name": "Prism Robotics",
        "industry": "Robotics & Hardware",
        "description": "Autonomous warehouse robotics and computer vision systems optimizing global supply chains.",
        "recruiter_email": "team@prismrobotics.tech",
        "jobs": [
            {
                "title": "Computer Vision & ML Engineer",
                "description": "Deploy real-time object detection models and spatial tracking systems on edge devices.",
                "required_skills": ["Python", "PyTorch", "OpenCV", "Deep Learning", "Linux", "C++"],
                "min_years_experience": 3,
                "salary_min": 155000,
                "salary_max": 205000,
                "location": "Austin, TX",
                "remote_ok": False,
                "seniority": "Senior",
            }
        ]
    },
    {
        "name": "Aether Commerce",
        "industry": "E-Commerce & Retail",
        "description": "Headless commerce platform providing ultra-fast shopping experiences and modular inventory orchestration.",
        "recruiter_email": "people@aethercommerce.com",
        "jobs": [
            {
                "title": "Principal Web Performance Engineer",
                "description": "Drive core web vitals and sub-second page loads across thousands of global merchant storefronts.",
                "required_skills": ["Next.js", "React", "TypeScript", "HTML5", "CSS3", "GraphQL"],
                "min_years_experience": 5,
                "salary_min": 170000,
                "salary_max": 220000,
                "location": "Remote",
                "remote_ok": True,
                "seniority": "Principal",
            }
        ]
    },
    {
        "name": "Chronos Analytics",
        "industry": "Data & Analytics",
        "description": "Time-series database and streaming analytics platform processing billions of telemetry events per second.",
        "recruiter_email": "jobs@chronosdata.com",
        "jobs": [
            {
                "title": "Lead Data Platform Engineer",
                "description": "Architect high-throughput real-time stream processing pipelines and automated analytical queries.",
                "required_skills": ["Python", "Kafka", "Redis", "PostgreSQL", "Docker", "REST API"],
                "min_years_experience": 4,
                "salary_min": 160000,
                "salary_max": 210000,
                "location": "Chicago, IL",
                "remote_ok": True,
                "seniority": "Lead",
            }
        ]
    },
    {
        "name": "OpenForge Studio",
        "industry": "Gaming & Web3",
        "description": "Creator studio and multiplayer game platform pioneering real-time procedural world generation.",
        "recruiter_email": "careers@openforge.gg",
        "jobs": [
            {
                "title": "Multiplayer Gameplay Engineer",
                "description": "Implement networked multiplayer synchronization, state serialization, and server authoritative simulations.",
                "required_skills": ["C++", "Python", "Go", "Git", "REST API", "Docker"],
                "min_years_experience": 3,
                "salary_min": 135000,
                "salary_max": 180000,
                "location": "Los Angeles, CA",
                "remote_ok": True,
                "seniority": "Senior",
            }
        ]
    },
    {
        "name": "Beacon Security",
        "industry": "Cybersecurity",
        "description": "Automated vulnerability scanning and compliance management for high-growth SaaS companies.",
        "recruiter_email": "security@beaconsec.io",
        "jobs": [
            {
                "title": "Application Security Engineer",
                "description": "Perform penetration testing, static code analysis, and design security guardrails across cloud applications.",
                "required_skills": ["Python", "Linux", "Docker", "AWS", "REST API", "Git"],
                "min_years_experience": 3,
                "salary_min": 145000,
                "salary_max": 195000,
                "location": "Remote",
                "remote_ok": True,
                "seniority": "Senior",
            }
        ]
    },
    {
        "name": "Lumina Creative",
        "industry": "Creative Tools",
        "description": "Next-generation collaborative canvas and 3D modeling tool running directly in WebGPU in the browser.",
        "recruiter_email": "hello@luminacreative.design",
        "jobs": [
            {
                "title": "Frontend Graphics Engineer",
                "description": "Build high-performance graphics pipelines, scene graphs, and vector manipulation UI in the browser.",
                "required_skills": ["TypeScript", "JavaScript", "React", "HTML5", "CSS3", "Framer Motion"],
                "min_years_experience": 3,
                "salary_min": 140000,
                "salary_max": 190000,
                "location": "San Francisco, CA",
                "remote_ok": True,
                "seniority": "Senior",
            }
        ]
    },
    {
        "name": "Kite Logistics",
        "industry": "Supply Chain & Logistics",
        "description": "Smart freight dispatching and carbon-neutral route optimization network.",
        "recruiter_email": "dispatch@kitelogistics.com",
        "jobs": [
            {
                "title": "Operations Systems Engineer",
                "description": "Build algorithmic load-matching engines and dispatch dashboards connecting carriers with shippers.",
                "required_skills": ["Python", "FastAPI", "PostgreSQL", "Celery", "Redis", "TypeScript"],
                "min_years_experience": 2,
                "salary_min": 125000,
                "salary_max": 165000,
                "location": "Atlanta, GA",
                "remote_ok": True,
                "seniority": "Mid-Senior",
            }
        ]
    },
    {
        "name": "Golang Gateway",
        "industry": "FinTech",
        "description": "High frequency trading systems and low latency microservices.",
        "recruiter_email": "recruiting@golanggateway.com",
        "jobs": [
            {
                "title": "Backend Engineer (Go)",
                "description": "Develop core services for our trading platform. Must have solid Go experience.",
                "required_skills": ["Go", "Docker", "PostgreSQL", "Redis"],
                "min_years_experience": 1,
                "salary_min": 110000,
                "salary_max": 150000,
                "location": "Remote",
                "remote_ok": True,
                "seniority": "Mid-Level",
            }
        ]
    },
    {
        "name": "C-Sharp Innovations",
        "industry": "Enterprise Software",
        "description": "Building the next generation of enterprise management tools using the .NET ecosystem.",
        "recruiter_email": "jobs@csharpinnovations.com",
        "jobs": [
            {
                "title": ".NET Developer",
                "description": "Build scalable APIs and services using C# and .NET Core.",
                "required_skills": ["C#", ".NET Core", "SQL Server", "Azure"],
                "min_years_experience": 2,
                "salary_min": 100000,
                "salary_max": 140000,
                "location": "Remote",
                "remote_ok": True,
                "seniority": "Mid-Level",
            }
        ]
    }
]


async def seed():
    print("Starting company and job listing seed process...")
    async with AsyncSessionLocal() as session:
        # Check existing companies
        existing_res = await session.execute(select(Company))
        existing_companies = existing_res.scalars().all()
        existing_names = {c.name for c in existing_companies}

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

            # Add Recruiter
            recruiter = Recruiter(
                company_id=company.id,
                email=comp_data["recruiter_email"],
                hashed_password=hash_password("Password123!"),
                role="owner",
            )
            session.add(recruiter)
            await session.flush()

            # Add Jobs
            for job_info in comp_data["jobs"]:
                # Generate embedding
                text = f"{job_info['title']} {job_info['description']} {' '.join(job_info['required_skills'])}"
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
        print(f"\n[SUCCESS] Successfully seeded {total_companies_created} companies and {total_jobs_created} jobs!")
        print("Candidate feed is now fully stocked and ready to swipe.")


if __name__ == "__main__":
    asyncio.run(seed())
