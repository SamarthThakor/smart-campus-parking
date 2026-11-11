from flask import current_app, jsonify, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .http import api, db, fail


@api.get("/")
def home():
    return render_template("index.html", demo=current_app.config["ALLOW_DEMO"])


@api.get("/privacy")
def privacy():
    return render_template("privacy.html")


@api.get("/api/health")
def health():
    try:
        with db().connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return fail("Database unavailable.", 503)
    return jsonify(status="ok")
