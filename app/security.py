"""Session checks, shared database throttling, and browser defenses."""

import hashlib
import hmac
import secrets
import time

from flask import current_app, g, request, session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .http import api, db, fail
from .models import auth_limits, auth_sessions, users


def epoch():
    return int(current_app.config.get("AUTH_CLOCK", time.time)())


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def throttle(email):
    """Fixed-window limits shared across workers and restarts.

    Count requests atomically, including successful requests. HMAC identifiers
    prevent the database from retaining raw IP addresses or attempted emails.
    The reverse proxy must supply REMOTE_ADDR; untrusted forwarding headers are
    deliberately ignored. This can conservatively group users behind one proxy.
    """
    if not current_app.config["RATE_LIMIT_ENABLED"]:
        return None
    timestamp = epoch()
    window = current_app.config["AUTH_WINDOW_SECONDS"]
    bucket = timestamp // window
    expires = (bucket + 1) * window
    subjects = [
        (
            "ip:" + (request.remote_addr or "unknown"),
            current_app.config["AUTH_IP_LIMIT"],
        )
    ]
    if email:
        subjects.append(
            ("account:" + email.lower(), current_app.config["AUTH_ACCOUNT_LIMIT"])
        )
    limited = False
    with db().begin() as conn:
        conn.execute(auth_limits.delete().where(auth_limits.c.expires_at <= timestamp))
        conn.execute(
            auth_sessions.delete().where(auth_sessions.c.expires_at <= timestamp)
        )
        for subject, maximum in subjects:
            key = hmac.new(
                current_app.secret_key.encode(),
                f"{bucket}:{subject}".encode(),
                hashlib.sha256,
            ).hexdigest()
            condition = auth_limits.c.key_hash == key
            updated = conn.execute(
                auth_limits.update()
                .where(condition)
                .values(attempts=auth_limits.c.attempts + 1)
            )
            if not updated.rowcount:
                try:
                    with conn.begin_nested():
                        conn.execute(
                            auth_limits.insert().values(
                                key_hash=key, attempts=1, expires_at=expires
                            )
                        )
                except IntegrityError:
                    conn.execute(
                        auth_limits.update()
                        .where(condition)
                        .values(attempts=auth_limits.c.attempts + 1)
                    )
            count = conn.execute(
                select(auth_limits.c.attempts).where(condition)
            ).scalar_one()
            limited = limited or count > maximum
    if limited:
        response, status = fail("Too many attempts. Try again later.", 429)
        response.headers["Retry-After"] = str(expires - timestamp)
        return response, status
    return None


def issue_session(user_id):
    token = secrets.token_urlsafe(32)
    with db().begin() as conn:
        conn.execute(
            auth_sessions.delete().where(auth_sessions.c.expires_at <= epoch())
        )
        conn.execute(
            auth_sessions.insert().values(
                token_hash=digest(token),
                user_id=user_id,
                expires_at=epoch() + current_app.config["SESSION_SECONDS"],
            )
        )
    session.clear()
    session.permanent = True
    session["auth_token"] = token


@api.before_request
def protect():
    if not request.path.startswith("/api/"):
        return None
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
        expected = session.get("csrf")
        supplied = request.headers.get("X-CSRF-Token", "")
        if not expected or not secrets.compare_digest(
            expected.encode(), supplied.encode()
        ):
            return fail("Missing or invalid CSRF token.", 403)
    if request.path in {
        "/api/health",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/csrf",
    }:
        return None
    token = session.get("auth_token")
    if not isinstance(token, str):
        return fail("Sign in first.", 401)
    with db().connect() as conn:
        row = (
            conn.execute(
                select(users)
                .join(auth_sessions, users.c.user_id == auth_sessions.c.user_id)
                .where(
                    auth_sessions.c.token_hash == digest(token),
                    auth_sessions.c.expires_at > epoch(),
                )
            )
            .mappings()
            .first()
        )
    if row is None:
        session.clear()
        return fail("Session expired. Sign in again.", 401)
    g.user = dict(row)
    if request.path.startswith("/api/admin/") and g.user["role"] != "admin":
        return fail("Administrator access required.", 403)


@api.after_app_request
def response_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if current_app.config["APP_ENV"] == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
