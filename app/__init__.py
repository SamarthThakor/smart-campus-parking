import os
import secrets
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
import click
from dotenv import load_dotenv
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from sqlalchemy import create_engine, event
from .models import metadata


class JSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(value):
        if isinstance(value, (time, datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return DefaultJSONProvider.default(value)


def create_app(config=None):
    load_dotenv()
    app = Flask(__name__)
    app.json = JSONProvider(app)
    Path(app.instance_path).mkdir(exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE_URL=os.environ.get(
            "DATABASE_URL",
            "sqlite:///"
            + str(Path(app.instance_path) / "parking.db").replace("\\", "/"),
        ),
        CAMPUS_TIMEZONE=os.environ.get("CAMPUS_TIMEZONE", "America/New_York"),
        APP_ENV=os.environ.get("APP_ENV", "development"),
        ALLOW_DEMO=os.environ.get("APP_ENV", "development") != "production",
        SESSION_SECONDS=3600,
        AUTH_WINDOW_SECONDS=900,
        AUTH_ACCOUNT_LIMIT=8,
        AUTH_IP_LIMIT=40,
        RATE_LIMIT_ENABLED=True,
        TRUSTED_HOSTS=[
            x.strip()
            for x in os.environ.get("TRUSTED_HOSTS", "").split(",")
            if x.strip()
        ]
        or None,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
        SESSION_REFRESH_EACH_REQUEST=False,
        SESSION_COOKIE_SECURE=os.environ.get("APP_HTTPS") == "1",
        MAX_CONTENT_LENGTH=16384,
    )
    if config:
        app.config.update(config)
    if app.config["APP_ENV"] == "production":
        if not os.environ.get("SECRET_KEY") or len(app.config["SECRET_KEY"]) < 32:
            raise RuntimeError(
                "Production requires a persistent SECRET_KEY of at least 32 characters."
            )
        if not app.config["SESSION_COOKIE_SECURE"] or not app.config["TRUSTED_HOSTS"]:
            raise RuntimeError("Production requires HTTPS cookies and TRUSTED_HOSTS.")
        app.config["ALLOW_DEMO"] = False
    ZoneInfo(app.config["CAMPUS_TIMEZONE"])
    engine = create_engine(app.config["DATABASE_URL"], pool_pre_ping=True)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    app.extensions["db"] = engine
    from .migrations import upgrade_database

    upgrade_database(engine)
    from .routes import api

    app.register_blueprint(api)

    @app.cli.command("init-db")
    def init_db():
        """Apply all pending versioned migrations."""
        upgrade_database(engine)
        click.echo("Database is at the latest migration.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Load fictional records into an initialized, empty database."""
        if not app.config["ALLOW_DEMO"]:
            raise click.ClickException("Demo accounts are disabled in production.")
        from .seed import seed_demo

        with engine.begin() as conn:
            seed_demo(conn)
        click.echo("Demo data loaded. Local demo password: DemoParking123!")

    from .commands import register_commands

    register_commands(app)
    return app
