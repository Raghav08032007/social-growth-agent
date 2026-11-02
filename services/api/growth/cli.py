import click
from flask import current_app
from sqlalchemy import select

from .costs import record_cost
from .db import transaction
from .models import Membership, SessionToken, User, VaultToken, Workspace
from .security import digest, issue_session


def register(app):
    @app.cli.command("configure-cost-policy")
    @click.option("--workspace-id", required=True)
    @click.option("--plan-price-paise", required=True, type=click.IntRange(0, 100_000_000))
    @click.option("--alert-percent", required=True, type=click.IntRange(0, 100))
    def configure_cost_policy(workspace_id, plan_price_paise, alert_percent):
        """Set monitoring thresholds only; this does not change billing or entitlements."""
        with transaction(current_app.extensions["engine"]) as db:
            row = db.get(Workspace, workspace_id)
            if row is None:
                raise click.ClickException("Workspace not found")
            row.plan_price_paise, row.cost_alert_percent = plan_price_paise, alert_percent
        click.echo("Updated cost monitoring policy; billing was not changed")

    @app.cli.command("provision")
    @click.option("--name", required=True)
    @click.option("--workspace", required=True)
    @click.option("--staff", is_flag=True)
    def provision(name, workspace, staff):
        """Trusted operator only. Print a one-hour opaque session once; never store it in files."""
        if not 1 <= len(name) <= 120 or not 1 <= len(workspace) <= 120:
            raise click.ClickException("Names must be 1–120 characters")
        with transaction(current_app.extensions["engine"]) as db:
            user, space = User(name=name, is_staff=staff), Workspace(name=workspace)
            db.add_all([user, space])
            db.flush()
            db.add(Membership(user_id=user.id, workspace_id=space.id, role="owner"))
            token = issue_session(db, user.id)
            click.echo(f"User: {user.id}\nWorkspace: {space.id}\nSession (one hour): {token}")

    @app.cli.command("session")
    @click.option("--user-id", required=True)
    def session(user_id):
        """Issue a replacement session for an existing user from a trusted operator terminal."""
        with transaction(current_app.extensions["engine"]) as db:
            if db.get(User, user_id) is None:
                raise click.ClickException("User not found")
            click.echo(issue_session(db, user_id))

    @app.cli.command("revoke-session")
    @click.option("--token", prompt=True, hide_input=True)
    def revoke_session(token):
        with transaction(current_app.extensions["engine"]) as db:
            row = db.get(SessionToken, digest(token))
            if row:
                row.revoked = True
        click.echo("Session revoked if present")

    @app.cli.command("rotate-vault")
    def rotate_vault():
        """Rewrap all non-revoked data keys; keep old key IDs until this succeeds."""
        with transaction(current_app.extensions["engine"]) as db:
            rows = db.scalars(select(VaultToken).where(VaultToken.revoked.is_(False)))
            count = 0
            for row in rows:
                current_app.extensions["vault"].rewrap(db, row.workspace_id, row.id)
                count += 1
        click.echo(f"Rewrapped {count} connections")

    @app.cli.command("record-diagnostic-cost")
    @click.option("--workspace-id", required=True)
    @click.option("--operation-key", required=True)
    @click.option("--amount-paise", required=True, type=click.IntRange(0, 100_000_000))
    def diagnostic_cost(workspace_id, operation_key, amount_paise):
        """Explicit local cost fixture; never represents a real model call."""
        if current_app.extensions["settings"].environment == "production":
            raise click.ClickException("Diagnostic cost injection is disabled in production")
        with transaction(current_app.extensions["engine"]) as db:
            if db.get(Workspace, workspace_id) is None:
                raise click.ClickException("Workspace not found")
            record_cost(db, workspace_id, operation_key, amount_paise)
        click.echo("Recorded diagnostic AI cost (no model was called)")
