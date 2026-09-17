"""Step 5 evaluation script — clean score distribution after embedding fix.

Run inside the container:
    docker compose exec backend python eval_scores.py

Produces:
  1. Full score distribution across all candidates x listings
  2. Score breakdown for 5 known-good hand-verified pairs
  3. Separation analysis to guide threshold decision
  4. Weighted vs flat skill overlap comparison
"""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import Candidate
from app.models.job_listing import JobListing
from app.services.matching_service import compute_match_score, passes_hard_filters, skill_overlap_ratio
from app.core.config import settings


# ── Helpers ───────────────────────────────────────────────────────────────────

def skill_overlap_flat(candidate_skills, job_skills):
    """Flat (unweighted) Jaccard-style overlap for comparison in Step 4."""
    if not job_skills:
        return 1.0
    if not candidate_skills:
        return 0.0
    candidate_set = {s.lower().strip() for s in candidate_skills}
    required = [
        (item["skill"] if isinstance(item, dict) else item).lower().strip()
        for item in job_skills
    ]
    return len(candidate_set & set(required)) / len(required)


def pct(v):
    return f"{v*100:.1f}%"


def bar(v, width=30):
    filled = int(v * width)
    return "█" * filled + "░" * (width - filled)


# ── Main ──────────────────────────────────────────────────────────────────────

async def evaluate():
    async with AsyncSessionLocal() as db:
        candidates = (await db.execute(select(Candidate))).scalars().all()
        listings = (await db.execute(
            select(JobListing).where(JobListing.is_active.is_(True))
        )).scalars().all()

        print(f"\n{'='*70}")
        print(f"  STEP 5 EVALUATION — {len(candidates)} candidates × {len(listings)} listings")
        print(f"{'='*70}\n")

        # ── 1. Full score distribution ────────────────────────────────────────
        print("── 1. FULL SCORE DISTRIBUTION ──────────────────────────────────────\n")

        all_scores = []
        for c in candidates:
            for j in listings:
                if not passes_hard_filters(c, j):
                    continue
                score = compute_match_score(c, j)
                all_scores.append((score.total, c.name, j.title, score.breakdown))

        all_scores.sort(reverse=True)

        buckets = {
            "90-100%": 0, "80-89%": 0, "70-79%": 0, "60-69%": 0,
            "50-59%": 0, "40-49%": 0, "35-39%": 0, "<35% (below threshold)": 0
        }
        for s, *_ in all_scores:
            if s >= 0.90: buckets["90-100%"] += 1
            elif s >= 0.80: buckets["80-89%"] += 1
            elif s >= 0.70: buckets["70-79%"] += 1
            elif s >= 0.60: buckets["60-69%"] += 1
            elif s >= 0.50: buckets["50-59%"] += 1
            elif s >= 0.40: buckets["40-49%"] += 1
            elif s >= 0.35: buckets["35-39%"] += 1
            else: buckets["<35% (below threshold)"] += 1

        total_pairs = len(all_scores)
        for label, count in buckets.items():
            b = bar(count / max(total_pairs, 1))
            print(f"  {label:30s} {b} {count:3d}")

        if all_scores:
            scores_only = [s for s, *_ in all_scores]
            print(f"\n  Total pairs passing hard filters : {total_pairs}")
            print(f"  Max  : {pct(max(scores_only))}")
            print(f"  Min  : {pct(min(scores_only))}")
            print(f"  Mean : {pct(sum(scores_only)/len(scores_only))}")
            above_threshold = sum(1 for s in scores_only if s >= settings.MATCH_SCORE_THRESHOLD)
            print(f"  Pairs above threshold ({pct(settings.MATCH_SCORE_THRESHOLD)}): {above_threshold}/{total_pairs}")

        # ── 2. Top 10 pairs ───────────────────────────────────────────────────
        print(f"\n── 2. TOP 10 SCORING PAIRS ─────────────────────────────────────────\n")
        for i, (total, cname, jtitle, bd) in enumerate(all_scores[:10], 1):
            emb = bd.get("embedding_similarity", 0)
            sk  = bd.get("skill_overlap", 0)
            exp = bd.get("experience_fit", 0)
            sal = bd.get("salary_overlap", 0)
            fb  = " [FALLBACK]" if bd.get("used_embedding_fallback") else ""
            print(f"  {i:2d}. {pct(total):6s}  {cname:15s} → {jtitle}{fb}")
            print(f"         emb={pct(emb)} sk={pct(sk)} exp={pct(exp)} sal={pct(sal)}")

        # ── 3. Known-good hand-verified pairs ─────────────────────────────────
        print(f"\n── 3. KNOWN-GOOD PAIR SPOT CHECKS ──────────────────────────────────\n")

        known_good = [
            # (candidate_name_fragment, job_title_fragment, why)
            ("Alex Rivera",  "Senior Full-Stack",     "Alex: TypeScript/React/Python/FastAPI/PostgreSQL/Docker — all required skills match"),
            ("Ajay K",       "Full-Stack Product",    "Ajay: TypeScript/React/Python/FastAPI/PostgreSQL — near-perfect Flowdesk fit"),
            ("shrey",        ".NET Developer",        "shrey: C#/.NET Core/Azure/SQL Server — all 4 required skills match"),
            ("raj",          "Operations Systems",    "raj: Python/FastAPI/PostgreSQL + Atlanta location — exact Kite Logistics fit"),
            ("Alex Rivera",  "AI Platform",           "Alex: Python/FastAPI/PostgreSQL/Docker — 4 of 4 required skills match"),
        ]

        for cname_frag, jtitle_frag, reason in known_good:
            c = next((x for x in candidates if cname_frag.lower() in x.name.lower()), None)
            j = next((x for x in listings if jtitle_frag.lower() in x.title.lower()), None)
            if not c or not j:
                print(f"  SKIP  '{cname_frag}' / '{jtitle_frag}' — not found")
                continue

            passes = passes_hard_filters(c, j)
            if not passes:
                print(f"  FAIL hard filter  {c.name} → {j.title}")
                continue

            score = compute_match_score(c, j)
            bd = score.breakdown
            fb = " [FALLBACK]" if bd.get("used_embedding_fallback") else ""
            verdict = "GOOD" if score.total >= 0.65 else ("BORDERLINE" if score.total >= 0.45 else "LOW — investigate")
            print(f"  [{verdict}] {pct(score.total):6s}  {c.name} → {j.title}{fb}")
            print(f"    Why: {reason}")
            print(f"    emb={pct(bd.get('embedding_similarity',0))}  sk={pct(bd.get('skill_overlap',0))}  exp={pct(bd.get('experience_fit',0))}  sal={pct(bd.get('salary_overlap',0))}")
            print()

        # ── 4. Weighted vs flat skill overlap comparison ───────────────────────
        print(f"── 4. WEIGHTED vs FLAT SKILL OVERLAP COMPARISON ────────────────────\n")
        print(f"  {'Candidate':15s}  {'Job':30s}  {'Flat':6s}  {'Weighted':8s}  {'Delta':6s}")
        print(f"  {'-'*75}")

        sample_pairs = [
            ("Alex Rivera",  "Senior Full-Stack"),
            ("Ajay K",       "Full-Stack Product"),
            ("shrey",        ".NET Developer"),
            ("raj",          "Operations Systems"),
            ("raj",          "AI Platform"),      # bad fit — has Python but not PyTorch
        ]
        for cname_frag, jtitle_frag in sample_pairs:
            c = next((x for x in candidates if cname_frag.lower() in x.name.lower()), None)
            j = next((x for x in listings if jtitle_frag.lower() in x.title.lower()), None)
            if not c or not j:
                continue
            c_skills = list(c.skills or [])
            j_skills = list(j.required_skills or [])
            flat     = skill_overlap_flat(c_skills, j_skills)
            weighted = skill_overlap_ratio(c_skills, j_skills)
            delta    = weighted - flat
            sign     = "+" if delta >= 0 else ""
            print(f"  {c.name:15s}  {j.title:30s}  {pct(flat):6s}  {pct(weighted):8s}  {sign}{pct(delta)}")

        print(f"\n  REQUIRED_SKILL_WEIGHT = {settings.REQUIRED_SKILL_WEIGHT}")
        print(f"  PREFERRED_SKILL_WEIGHT = {settings.PREFERRED_SKILL_WEIGHT}")

        # ── Summary recommendation ─────────────────────────────────────────────
        print(f"\n── SUMMARY & THRESHOLD RECOMMENDATION ───────────────────────────────\n")
        if all_scores:
            scores_only = [s for s, *_ in all_scores]
            good_pairs = [s for s, cn, jt, _ in all_scores
                          if any(g[0].lower() in cn.lower() and g[1].lower() in jt.lower()
                                 for g in [("Alex", "Full-Stack"), ("Ajay", "Flowdesk"),
                                           ("shrey", ".NET"), ("raj", "Kite")])]
            if good_pairs:
                print(f"  Known-good pair scores  : {', '.join(pct(s) for s in sorted(good_pairs, reverse=True))}")
            non_good = [s for s in scores_only if s not in good_pairs]
            if non_good:
                avg_non_good = sum(non_good) / len(non_good)
                print(f"  Avg score (other pairs) : {pct(avg_non_good)}")
            print(f"  Current threshold       : {pct(settings.MATCH_SCORE_THRESHOLD)}")
            print()
            print("  Interpretation:")
            print("  - If known-good pairs score 70%+: pipeline is healthy, threshold of 0.35 is conservative (good).")
            print("  - If known-good pairs score <50%: still a bug in scoring weights or embeddings.")
            print("  - Flat vs weighted delta shows whether skill tiering is adding meaningful signal.")


if __name__ == "__main__":
    asyncio.run(evaluate())
