import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.matching_service import compute_match_score, passes_hard_filters

class MockCandidate:
    def __init__(self, years, min_sal, max_sal, loc, remote, skills):
        self.years_experience = years
        self.desired_salary_min = min_sal
        self.desired_salary_max = max_sal
        self.location = loc
        self.remote_ok = remote
        self.skills = skills
        self.profile_embedding = None

class MockJob:
    def __init__(self, min_years, min_sal, max_sal, loc, remote, skills):
        self.min_years_experience = min_years
        self.salary_min = min_sal
        self.salary_max = max_sal
        self.location = loc
        self.remote_ok = remote
        self.required_skills = skills
        self.listing_embedding = None
        self.is_active = True

candidate = MockCandidate(
    years=4,
    min_sal=130000,
    max_sal=195000,
    loc="San Francisco, CA",
    remote=True,
    skills=["TypeScript", "React", "Next.js", "Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "Celery"]
)

job = MockJob(
    min_years=3,
    min_sal=140000,
    max_sal=185000,
    loc="San Francisco, CA",
    remote=True,
    skills=["TypeScript", "React", "Next.js", "Python", "FastAPI", "PostgreSQL"]
)

if __name__ == "__main__":
    passes = passes_hard_filters(candidate, job)
    print(f"Passes Hard Filters: {passes}")
    
    score = compute_match_score(candidate, job)
    print(f"Score Total: {score.total}")
    print(f"Score Breakdown: {score.breakdown}")
