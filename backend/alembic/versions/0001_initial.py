"""Initial schema: all tables + pgvector + RLS policies

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── candidates ──────────────────────────────────────────────────────────
    op.create_table(
        "candidates",
        sa.Column("id", sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("resume_summary", sa.Text(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("desired_salary_min", sa.Integer(), nullable=True),
        sa.Column("desired_salary_max", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("remote_ok", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("profile_embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_candidates_email", "candidates", ["email"])

    # ── companies ────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_companies_tenant_id", "companies", ["tenant_id"])

    # ── recruiters ───────────────────────────────────────────────────────────
    op.create_table(
        "recruiters",
        sa.Column("id", sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="recruiter"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_recruiters_email", "recruiters", ["email"])
    op.create_index("ix_recruiters_company_id", "recruiters", ["company_id"])

    # ── job_listings ─────────────────────────────────────────────────────────
    op.create_table(
        "job_listings",
        sa.Column("id", sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required_skills", sa.JSON(), nullable=True),
        sa.Column("min_years_experience", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("remote_ok", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("seniority", sa.String(100), nullable=True),
        sa.Column("listing_embedding", Vector(384), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_job_listings_company_id", "job_listings", ["company_id"])
    op.create_index("ix_job_listings_tenant_id", "job_listings", ["tenant_id"])
    op.create_index("ix_job_listings_is_active", "job_listings", ["is_active"])

    # ── swipes ───────────────────────────────────────────────────────────────
    # Candidate-only — no swiped_by column.
    # unique(candidate_id, job_listing_id) prevents duplicate swipes.
    op.create_table(
        "swipes",
        sa.Column("id", sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("candidate_id", sa.Uuid(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("job_listing_id", sa.Uuid(), sa.ForeignKey("job_listings.id"), nullable=False),
        sa.Column("direction", sa.Enum("left", "right", name="swipedirection"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("candidate_id", "job_listing_id", name="uq_swipe_pair"),
    )
    op.create_index("ix_swipes_candidate_id", "swipes", ["candidate_id"])
    op.create_index("ix_swipes_job_listing_id", "swipes", ["job_listing_id"])

    # ── matches ───────────────────────────────────────────────────────────────
    # No 'pending' status — created automatically when score >= threshold.
    # Default status is 'applied'; the application record is created in the same transaction.
    op.create_table(
        "matches",
        sa.Column("id", sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("candidate_id", sa.Uuid(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("job_listing_id", sa.Uuid(), sa.ForeignKey("job_listings.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("score_breakdown", sa.JSON(), nullable=True),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column(
            "status",
            sa.Enum("applied", "withdrawn", name="matchstatus"),
            nullable=False,
            server_default="applied",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_matches_candidate_id", "matches", ["candidate_id"])
    op.create_index("ix_matches_job_listing_id", "matches", ["job_listing_id"])

    # ── applications ──────────────────────────────────────────────────────────
    # Company updates status post-hoc via PATCH /company/applications/{id}.
    # Rejection is a status update — it never deletes or un-submits the application.
    # Only 'rejected' and 'interview' are valid company-side transitions.
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("match_id", sa.Uuid(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("job_listing_id", sa.Uuid(), sa.ForeignKey("job_listings.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("submitted", "viewed", "rejected", "interview", name="applicationstatus"),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        # Prevent double-application for the same candidate+listing
        sa.UniqueConstraint("candidate_id", "job_listing_id", name="uq_application_pair"),
    )
    op.create_index("ix_applications_match_id", "applications", ["match_id"])
    op.create_index("ix_applications_candidate_id", "applications", ["candidate_id"])
    op.create_index("ix_applications_job_listing_id", "applications", ["job_listing_id"])

    # ── Row-Level Security ────────────────────────────────────────────────────
    for table in ("companies", "job_listings"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    for table in ("companies", "job_listings"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("applications")
    op.drop_table("matches")
    op.drop_table("swipes")
    op.drop_table("job_listings")
    op.drop_table("recruiters")
    op.drop_table("companies")
    op.drop_table("candidates")

    op.execute("DROP TYPE IF EXISTS applicationstatus")
    op.execute("DROP TYPE IF EXISTS matchstatus")
    op.execute("DROP TYPE IF EXISTS swipedirection")
