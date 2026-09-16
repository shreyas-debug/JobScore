"""Migrate required_skills from flat list[str] to list[{skill, level}]

Revision ID: 0002_skill_levels
Revises: 0001_initial
Create Date: 2026-09-16

"""
from __future__ import annotations

import json
from alembic import op
from sqlalchemy import text

revision = "0002_skill_levels"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, required_skills FROM job_listings WHERE required_skills IS NOT NULL")
    ).fetchall()

    for row in rows:
        skills = row.required_skills
        if not skills:
            continue
        # Already migrated (first item is a dict) — skip
        if isinstance(skills[0], dict):
            continue
        # Legacy flat list[str] — treat every existing skill as "required"
        new_value = [{"skill": s, "level": "required"} for s in skills]
        conn.execute(
            text("UPDATE job_listings SET required_skills = :v WHERE id = :id"),
            {"v": json.dumps(new_value), "id": str(row.id)},
        )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, required_skills FROM job_listings WHERE required_skills IS NOT NULL")
    ).fetchall()

    for row in rows:
        skills = row.required_skills
        if not skills:
            continue
        # Already flat strings — skip
        if isinstance(skills[0], str):
            continue
        # Revert dicts back to flat string list
        flat = [s["skill"] for s in skills]
        conn.execute(
            text("UPDATE job_listings SET required_skills = :v WHERE id = :id"),
            {"v": json.dumps(flat), "id": str(row.id)},
        )
