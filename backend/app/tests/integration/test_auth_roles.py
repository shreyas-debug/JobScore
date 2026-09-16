from __future__ import annotations

import pytest

from app.tests.conftest import auth_header, login_as_candidate


@pytest.mark.asyncio
async def test_candidate_token_rejected_on_company_only_route(client, seed_candidate):
    token = login_as_candidate(seed_candidate)
    resp = await client.post(
        "/api/v1/company/jobs",
        json={"title": "Hacker Job", "min_years_experience": 0},
        headers=auth_header(token),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_inactive_job_listing_excluded_from_candidate_feed(client, seed_candidate, db):
    import uuid
    from app.models.company import Company
    from app.models.job_listing import JobListing

    tenant_id = uuid.uuid4()
    company = Company(name="Inactive Test Corp", tenant_id=tenant_id)
    db.add(company)
    await db.flush()
    inactive_job = JobListing(
        company_id=company.id,
        tenant_id=tenant_id,
        title="Hidden Job",
        min_years_experience=0,
        is_active=False,
    )
    db.add(inactive_job)
    await db.commit()

    token = login_as_candidate(seed_candidate)
    feed = await client.get("/api/v1/candidate/feed", headers=auth_header(token))
    assert feed.status_code == 200
    feed_ids = [j["id"] for j in feed.json()["items"]]
    assert str(inactive_job.id) not in feed_ids


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401(client):
    resp = await client.get("/api/v1/candidate/feed")
    assert resp.status_code in (401, 403)  # HTTPBearer returns 403 on missing header
