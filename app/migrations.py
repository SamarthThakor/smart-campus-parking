"""Apply versioned migrations before the application accepts requests."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

def upgrade_database(engine):
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        if tables and "alembic_version" not in tables:
            raise RuntimeError("Unversioned database detected. Preserve your MS2 database and use a new DATABASE_URL; do not delete existing data.")
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        version = connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
        print(f"Database migration complete: {version}", flush=True)
