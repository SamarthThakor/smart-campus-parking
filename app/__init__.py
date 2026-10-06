import os
import secrets
from datetime import datetime, time
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
        if isinstance(value,(time,datetime)):
            return value.isoformat()
        if isinstance(value,Decimal):
            return float(value)
        return DefaultJSONProvider.default(value)

def create_app(config=None):
    load_dotenv()
    app=Flask(__name__); app.json=JSONProvider(app)
    Path(app.instance_path).mkdir(exist_ok=True)
    app.config.from_mapping(SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE_URL=os.environ.get("DATABASE_URL","sqlite:///"+str(Path(app.instance_path)/"parking.db").replace("\\","/")),
        CAMPUS_TIMEZONE=os.environ.get("CAMPUS_TIMEZONE","America/New_York"),
        SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("APP_HTTPS")=="1",MAX_CONTENT_LENGTH=16384)
    if config: app.config.update(config)
    ZoneInfo(app.config["CAMPUS_TIMEZONE"])
    engine=create_engine(app.config["DATABASE_URL"],pool_pre_ping=True)
    if engine.dialect.name=="sqlite":
        @event.listens_for(engine,"connect")
        def foreign_keys(connection,_):
            connection.execute("PRAGMA foreign_keys=ON")
    app.extensions["db"]=engine
    from .routes import api
    app.register_blueprint(api)
    @app.cli.command("init-db")
    def init_db():
        """Create missing tables. Existing schemas are not migrated."""
        metadata.create_all(engine); click.echo("Database tables initialized.")
    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Load fictional records into an initialized, empty database."""
        from .seed import seed_demo
        with engine.begin() as conn: seed_demo(conn)
        click.echo("Demo data loaded. Local demo password: DemoParking123!")
    return app

