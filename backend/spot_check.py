"""Spot-check rejected and low-scoring pairs to confirm algorithm correctness."""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import Candidate
from app.models.job_listing import JobListing
from app.services.matching_service import compute_match_score, passes_hard_filters


def fmt(v): return f"{v*100:.1f}%"


async def spot_check():
    async with AsyncSessionLocal() as db:
        candidates = (await db.execute(select(Candidate))).scalars().all()
        listings = (await db.execute(
            select(JobListing).where(JobListing.is_active.is_(True))
        )).scalars().all()

        total_pairs = len(candidates) * len(listings)

        # ── Hard filter rejections ────────────────────────────────────────────
        print("=" * 65)
        print("  HARD FILTER REJECTIONS")
        print("=" * 65)
        rejected = [(c, j) for c in candidates for j in listings
                    if not passes_hard_filters(c, j)]
        print(f"Rejected: {len(rejected)} / {total_pairs}  "
              f"({len(rejected)/total_pairs*100:.0f}% of full pool)\n")

        for c, j in rejected[:10]:
            c_skills = {s.lower() for s in (c.skills or [])}
            j_req = [
                (s["skill"] if isinstance(s, dict) else s).lower()
                for s in (j.required_skills or [])
                if not isinstance(s, dict) or s.get("level") == "required"
            ]
            matched = [s for s in j_req if s in c_skills]

            # Diagnose which hard filter fired
            reasons = []
            if c.years_experience < j.min_years_experience:
                reasons.append(f"exp {c.years_experience}y < min {j.min_years_experience}y")
            if (c.desired_salary_min and c.desired_salary_max and
                    j.salary_min and j.salary_max):
                if c.desired_salary_min > j.salary_max or j.salary_min > c.desired_salary_max:
                    reasons.append(f"salary mismatch c={c.desired_salary_min/1000:.0f}-{c.desired_salary_max/1000:.0f}k j={j.salary_min/1000:.0f}-{j.salary_max/1000:.0f}k")
            if j_req and not matched:
                reasons.append(f"zero required skills matched ({j_req[:3]})")
            if not reasons:
                reasons.append("location/remote mismatch")

            verdict = "CORRECT" if reasons else "REVIEW"
            print(f"  [{verdict}]  {c.name} -> {j.title}")
            print(f"    Filter: {' | '.join(reasons)}")
            print(f"    Candidate skills: {list(c.skills or [])[:5]}")
            print()

        # ── Low scorers (<=50%, passed hard filters) ──────────────────────────
        print("=" * 65)
        print("  LOW SCORERS (<=50%, passed hard filters)")
        print("=" * 65)
        low = []
        for c in candidates:
            for j in listings:
                if passes_hard_filters(c, j):
                    score = compute_match_score(c, j)
                    if score.total <= 0.50:
                        low.append((score.total, c, j, score.breakdown))
        low.sort()

        print(f"Low scorers: {len(low)} pairs\n")
        for total, c, j, bd in low:
            emb = bd.get("embedding_similarity", 0)
            sk = bd.get("skill_overlap", 0)
            exp = bd.get("experience_fit", 0)
            sal = bd.get("salary_overlap", 0)
            c_skills = {s.lower() for s in (c.skills or [])}
            j_req = [
                (s["skill"] if isinstance(s, dict) else s).lower()
                for s in (j.required_skills or [])
                if not isinstance(s, dict) or s.get("level") == "required"
            ]
            matched = [s for s in j_req if s in c_skills]

            # Judge correctness
            domain_mismatch = len(matched) == 0 or len(matched) / max(len(j_req), 1) < 0.4
            verdict = "CORRECT" if domain_mismatch else "REVIEW"
            print(f"  [{verdict}]  {fmt(total)}  {c.name} -> {j.title}")
            print(f"    emb={fmt(emb)} sk={fmt(sk)} exp={fmt(exp)} sal={fmt(sal)}")
            print(f"    required: {j_req[:4]}  |  candidate matched: {matched}")
            print()

        # ── Summary ───────────────────────────────────────────────────────────
        print("=" * 65)
        print("  FUNNEL SUMMARY")
        print("=" * 65)
        passed_hard = total_pairs - len(rejected)
        passed_soft = sum(
            1 for c in candidates for j in listings
            if passes_hard_filters(c, j) and compute_match_score(c, j).total >= 0.60
        )
        print(f"  Full pool          : {total_pairs}")
        print(f"  Pass hard filters  : {passed_hard}  ({passed_hard/total_pairs*100:.0f}%)")
        print(f"  Pass soft (>=60%)  : {passed_soft}  ({passed_soft/total_pairs*100:.0f}% of full pool)")
        print(f"  Rejected entirely  : {total_pairs - passed_soft}  ({(total_pairs-passed_soft)/total_pairs*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(spot_check())
