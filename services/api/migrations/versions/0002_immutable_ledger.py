"""Enforce append-only audit and credit entries at the database boundary."""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    dialect = op.get_bind().dialect.name
    for table in ("agent_actions", "credits_ledger"):
        for action in ("UPDATE", "DELETE"):
            name = f"{table}_immutable_{action.lower()}"
            if dialect == "sqlite":
                op.execute(
                    f"CREATE TRIGGER {name} BEFORE {action} ON {table} "
                    "BEGIN SELECT RAISE(ABORT, 'append-only record'); END"
                )
            elif dialect == "mysql":
                op.execute(
                    f"CREATE TRIGGER {name} BEFORE {action} ON {table} FOR EACH ROW "
                    "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only record'"
                )
            else:
                raise RuntimeError("Append-only migrations support only SQLite tests and MySQL")


def downgrade():
    for table in ("agent_actions", "credits_ledger"):
        for action in ("update", "delete"):
            op.execute(f"DROP TRIGGER IF EXISTS {table}_immutable_{action}")
