"""Shared JSON contract and request helpers; no domain rules."""

import secrets
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

api = Blueprint("api", __name__)


def fail(message, status=400):
    return jsonify(error=dict(code=status, message=message)), status


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("A JSON object is required.")
    return data


def db():
    return current_app.extensions["db"]


def now():
    return current_app.config.get(
        "NOW", lambda: datetime.now(ZoneInfo(current_app.config["CAMPUS_TIMEZONE"]))
    )()


def csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(24)
    return session["csrf"]


@api.app_errorhandler(ValueError)
def invalid(error):
    return fail(str(error))


@api.app_errorhandler(LookupError)
def missing(error):
    return fail(str(error), 404)


@api.app_errorhandler(SQLAlchemyError)
def database_error(error):
    # SQL exception text can contain parameter values. Do not log that payload.
    current_app.logger.error("Database operation failed (%s)", type(error).__name__)
    return fail("Database operation failed.", 500)


@api.app_errorhandler(HTTPException)
def http_error(error):
    return fail(error.description, error.code)
