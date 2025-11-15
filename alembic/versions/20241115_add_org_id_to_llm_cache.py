"""Add organization_id to llm_cache.

Revision ID: 20241115_add_org_id
Revises: 518cd8c69c18
Create Date: 2025-11-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20241115_add_org_id"
down_revision = "518cd8c69c18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(
            sa.Column("api_key_digest", sa.String(length=64), nullable=True)
        )
        batch_op.create_index(
            "idx_organizations_api_key_digest",
            ["api_key_digest"],
            unique=True,
        )

    with op.batch_alter_table("llm_cache") as batch_op:
        batch_op.add_column(
            sa.Column(
                "organization_id",
                sa.Integer(),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "fk_llm_cache_org_id",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(
            "idx_llm_cache_organization_id",
            ["organization_id"],
            unique=False,
        )

    # Backfill existing rows with sentinel value 0 to keep history accessible.
    op.execute(
        sa.text(
            "UPDATE llm_cache SET organization_id = 0 WHERE organization_id IS NULL"
        )
    )

    with op.batch_alter_table("llm_cache") as batch_op:
        batch_op.alter_column(
            "organization_id",
            existing_type=sa.Integer(),
            nullable=False,
            existing_server_default=None,
        )

    with op.batch_alter_table("schema_validation_logs") as batch_op:
        batch_op.alter_column(
            "llm_response",
            existing_type=sa.Text(),
            type_=postgresql.JSONB(),
            postgresql_using="llm_response::jsonb",
        )


def downgrade() -> None:
    with op.batch_alter_table("schema_validation_logs") as batch_op:
        batch_op.alter_column(
            "llm_response",
            existing_type=postgresql.JSONB(),
            type_=sa.Text(),
            postgresql_using="llm_response::text",
        )

    with op.batch_alter_table("llm_cache") as batch_op:
        batch_op.drop_index("idx_llm_cache_organization_id")
        batch_op.drop_constraint("fk_llm_cache_org_id", type_="foreignkey")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_index("idx_organizations_api_key_digest")
        batch_op.drop_column("api_key_digest")

