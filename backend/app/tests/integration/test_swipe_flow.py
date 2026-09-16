from __future__ import annotations

import pytest

from app.tests.conftest import auth_header, login_as_candidate, login_as_recruiter


@pytest.mark.asyncio
async def test_right_swipe_above_threshold_auto_creates_match_and_application(
    client, seed_candidate, seed_job_high_fit
):
    """Candidate right-swipe that clears threshold → Match + Application in one transaction.

    No company action taken yet — the application is already 'submitted'.
    """
    job, company, recruiter = seed_job_high_fit
    token = login_as_candidate(seed_candidate)

    r = await client.post(
        "/api/v1/candidate/swipe",
        json={"job_listing_id": str(job.id), "direction": "right"},
        headers=auth_header(token),
    )
    assert r.status_code == 200

    # Candidate can see the match immediately
    matches_resp = await client.get("/api/v1/candidate/matches", headers=auth_header(token))
    assert matches_resp.status_code == 200
    job_ids = [m["job_listing_id"] for m in matches_resp.json()]
    assert str(job.id) in job_ids

    # Company can see it in their applications list — no action required
    recruiter_token = login_as_recruiter(recruiter, company.tenant_id)
    apps_resp = await client.get(
        f"/api/v1/company/jobs/{job.id}/applications",
        headers=auth_header(recruiter_token),
    )
    assert apps_resp.status_code == 200
    candidate_ids = [a["candidate_id"] for a in apps_resp.json()]
    assert str(seed_candidate.id) in candidate_ids
    assert apps_resp.json()[0]["status"] == "submitted"


@pytest.mark.asyncio
async def test_right_swipe_below_threshold_never_reaches_company(
    client, seed_candidate, seed_job_low_fit
):
    """A right-swipe scoring below 0.60 is recorded but creates no match/application."""
    job, company, recruiter = seed_job_low_fit
    token = login_as_candidate(seed_candidate)

    await client.post(
        "/api/v1/candidate/swipe",
        json={"job_listing_id": str(job.id), "direction": "right"},
        headers=auth_header(token),
    )

    matches = await client.get("/api/v1/candidate/matches", headers=auth_header(token))
    assert matches.json() == []

    recruiter_token = login_as_recruiter(recruiter, company.tenant_id)
    apps = await client.get(
        f"/api/v1/company/jobs/{job.id}/applications",
        headers=auth_header(recruiter_token),
    )
    assert apps.json() == []


@pytest.mark.asyncio
async def test_company_reject_does_not_retract_the_application(
    client, seed_candidate, seed_job_high_fit
):
    """Rejection is a status update, not a deletion. Match stays visible to candidate."""
    job, company, recruiter = seed_job_high_fit
    token = login_as_candidate(seed_candidate)

    await client.post(
        "/api/v1/candidate/swipe",
        json={"job_listing_id": str(job.id), "direction": "right"},
        headers=auth_header(token),
    )

    recruiter_token = login_as_recruiter(recruiter, company.tenant_id)
    apps_resp = await client.get(
        f"/api/v1/company/jobs/{job.id}/applications",
        headers=auth_header(recruiter_token),
    )
    application_id = apps_resp.json()[0]["id"]

    reject_resp = await client.patch(
        f"/api/v1/company/applications/{application_id}",
        json={"status": "rejected"},
        headers=auth_header(recruiter_token),
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    # Candidate still sees their match — rejection never un-submits
    matches = await client.get("/api/v1/candidate/matches", headers=auth_header(token))
    assert str(job.id) in [m["job_listing_id"] for m in matches.json()]


@pytest.mark.asyncio
async def test_recruiter_cannot_move_application_to_submitted(
    client, seed_candidate, seed_job_high_fit
):
    """Setting status to 'submitted' from the recruiter side must be rejected (422)."""
    job, company, recruiter = seed_job_high_fit
    token = login_as_candidate(seed_candidate)

    await client.post(
        "/api/v1/candidate/swipe",
        json={"job_listing_id": str(job.id), "direction": "right"},
        headers=auth_header(token),
    )

    recruiter_token = login_as_recruiter(recruiter, company.tenant_id)
    apps_resp = await client.get(
        f"/api/v1/company/jobs/{job.id}/applications",
        headers=auth_header(recruiter_token),
    )
    application_id = apps_resp.json()[0]["id"]

    resp = await client.patch(
        f"/api/v1/company/applications/{application_id}",
        json={"status": "submitted"},
        headers=auth_header(recruiter_token),
    )
    # 'submitted' is not a valid company-side transition
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_swipe_is_idempotent_not_duplicated(client, seed_candidate, seed_job):
    job, *_ = seed_job
    token = login_as_candidate(seed_candidate)
    payload = {"job_listing_id": str(job.id), "direction": "right"}

    r1 = await client.post("/api/v1/candidate/swipe", json=payload, headers=auth_header(token))
    assert r1.status_code == 200

    r2 = await client.post("/api/v1/candidate/swipe", json=payload, headers=auth_header(token))
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_left_swipe_never_triggers_score_computation(client, seed_candidate, seed_job, mocker):
    job, *_ = seed_job
    spy = mocker.spy(
        __import__("app.services.matching_service", fromlist=["compute_match_score"]),
        "compute_match_score",
    )
    token = login_as_candidate(seed_candidate)
    await client.post(
        "/api/v1/candidate/swipe",
        json={"job_listing_id": str(job.id), "direction": "left"},
        headers=auth_header(token),
    )
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_daily_swipe_cap_is_enforced(client, seed_candidate, db):
    """(cap+1)th swipe in a day returns 429 with a Retry-After header."""
    import uuid
    from app.models.company import Company
    from app.models.job_listing import JobListing
    from app.core.config import settings

    cap = settings.DAILY_SWIPE_CAP
    token = login_as_candidate(seed_candidate)

    tenant_id = uuid.uuid4()
    company = Company(name="Cap Test Corp", tenant_id=tenant_id)
    db.add(company)
    await db.flush()
    jobs = []
    for _ in range(cap + 1):
        job = JobListing(
            company_id=company.id, tenant_id=tenant_id,
            title="Test Job", min_years_experience=0, is_active=True,
        )
        db.add(job)
        jobs.append(job)
    await db.commit()

    for job in jobs[:cap]:
        r = await client.post(
            "/api/v1/candidate/swipe",
            json={"job_listing_id": str(job.id), "direction": "left"},
            headers=auth_header(token),
        )
        assert r.status_code == 200

    over_cap = await client.post(
        "/api/v1/candidate/swipe",
        json={"job_listing_id": str(jobs[cap].id), "direction": "left"},
        headers=auth_header(token),
    )
    assert over_cap.status_code == 429
    assert "Retry-After" in over_cap.headers
