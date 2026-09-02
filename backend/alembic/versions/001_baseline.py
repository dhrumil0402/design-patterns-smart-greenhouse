"""baseline

Revision ID: 001_baseline
Revises:
Create Date: 2026-09-02

Empty baseline revision. It exists to prove the Alembic + PostgreSQL
migration toolchain runs end-to-end. No business tables are created in
Phase 1 — Phase 2 adds the `devices` table on top of this baseline.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Intentionally empty: this phase only proves migrations run.
    pass


def downgrade() -> None:
    # Intentionally empty.
    pass