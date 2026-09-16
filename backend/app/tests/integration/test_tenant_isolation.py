from __future__ import annotations

import pytest
from sqlalchemy import text

from app.tests.conftest import auth_header, login_as_recruiter


@pytest.mark.asyncio
async def test_recruiter_cannot_see_another_companys_jobs(client, seed_two_companies, db):
    company_a, company_b = seed_two_companies
    token_a = login_as_recruiter(company_a.recruiter, company_a.tenant_id)
    resp = await client.get("/api/v1/company/jobs", headers=auth_header(token_a))
    assert resp.status_code == 200
    returned_ids = {job["id"] for job in resp.json()}
    company_b_job_ids = {str(j.id) for j in company_b.jobs}
    assert not returned_ids & company_b_job_ids


@pytest.mark.asyncio
async def test_rls_blocks_raw_query_even_without_orm_filter(db, seed_two_companies):
    company_a, company_b = seed_two_companies
    # Set tenant to company_a — raw query must only see company_a's jobs
    await db.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(company_a.tenant_id)})
    rows = (await db.execute(text("SELECT company_id FROM job_listings"))).fetchall()
    company_b_id = str(company_b.id)
    assert all(str(r[0]) != company_b_id for r in rows)
