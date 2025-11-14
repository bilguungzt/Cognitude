"""placeholder migration to restore missing revision

Revision ID: 518cd8c69c18
Revises: f5cd1fa3c00e
Create Date: 2025-11-14

This is a minimal placeholder migration created to restore Alembic's revision
graph. It intentionally performs no schema changes. Once Alembic graph is
restored, consider replacing this with the original migration content from
backup or commit history if available.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '518cd8c69c18'
down_revision = 'f5cd1fa3c00e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # placeholder — no-op
    pass


def downgrade() -> None:
    # placeholder — no-op
    pass
