"""Operator commands avoid public administrator signup and demo passwords."""

import click
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from .auth import credentials
from .models import users


def register_commands(app):
    @app.cli.command("init-catalog")
    def init_catalog():
        """Load fictional alpha lots, permits and building without demo accounts."""
        from .seed import seed_catalog

        with app.extensions["db"].begin() as conn:
            seed_catalog(conn)
        click.echo("Alpha catalog ready. Locations and availability are fictional.")

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_admin(email, password):
        """Create an administrator from the host's private operator console."""
        try:
            email, password = credentials(
                {"email": email, "password": password}, registration=True
            )
        except ValueError as error:
            raise click.ClickException(str(error)) from error
        with app.extensions["db"].begin() as conn:
            if conn.execute(
                select(users.c.user_id).where(users.c.email == email)
            ).first():
                raise click.ClickException(
                    "That account already exists; no role was changed."
                )
            conn.execute(
                users.insert().values(
                    email=email,
                    password_hash=generate_password_hash(password),
                    role="admin",
                )
            )
        click.echo("Administrator created.")
