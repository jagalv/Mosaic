"""mosaic_app non-superuser application role (Milestone 4b fix)

The API must NOT connect as the bootstrap superuser `mosaic` — a superuser
bypasses RLS unconditionally, so the watchlist policies (0007) never apply.
This creates a dedicated NON-superuser, NON-bypassrls role `mosaic_app` that the
API connects as, so RLS is actually enforced.

Grants are intentionally coarse (CRUD on all tables): per-row filtering is done
by RLS (FORCED on the user-owned tables), the same model Supabase uses. ALTER
DEFAULT PRIVILEGES covers future tables (e.g. M4c `notes`) automatically, since
migrations run as `mosaic`.

Runs as the admin role `mosaic`. The dev password matches the mosaic/mosaic dev
convention — rotate it (and APP_DATABASE_URL) for any real deployment.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mosaic_app') THEN
            CREATE ROLE mosaic_app LOGIN NOSUPERUSER NOBYPASSRLS
              PASSWORD 'mosaic_app';
          END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO mosaic_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
        "TO mosaic_app"
    )
    op.execute(
        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mosaic_app"
    )
    # Future tables/sequences created by the admin role (migrations) are covered
    # automatically — so M4c `notes` etc. need no extra grant.
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mosaic_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO mosaic_app"
    )


def downgrade() -> None:
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM mosaic_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE USAGE, SELECT ON SEQUENCES FROM mosaic_app"
    )
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM mosaic_app")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM mosaic_app")
    op.execute("REVOKE USAGE ON SCHEMA public FROM mosaic_app")
    op.execute("DROP ROLE IF EXISTS mosaic_app")
