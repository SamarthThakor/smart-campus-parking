"""Account creation and authentication endpoints."""

import re
from flask import jsonify, session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from .http import api, body, csrf, db, fail
from .models import auth_sessions, users
from .security import digest, issue_session, throttle

# Same password work for unknown accounts; never a valid user credential.
_DUMMY_HASH = generate_password_hash("unused-constant-for-timing-only")


def credentials(data, registration=False):
    if set(data) - {"email", "password"}:
        raise ValueError("Only email and password are accepted.")
    email, password = data.get("email"), data.get("password")
    if (
        not isinstance(email, str)
        or len(email) > 255
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
    ):
        raise ValueError("Enter a valid email address.")
    minimum = 12 if registration else 1
    if not isinstance(password, str) or not minimum <= len(password) <= 128:
        raise ValueError(f"Password must contain {minimum} to 128 characters.")
    return email.lower(), password


@api.get("/api/auth/csrf")
def token():
    return jsonify(csrf_token=csrf())


@api.post("/api/auth/register")
def register():
    email, password = credentials(body(), registration=True)
    limited = throttle(email)
    if limited:
        return limited
    password_hash = generate_password_hash(password)
    try:
        with db().begin() as conn:
            result = conn.execute(
                users.insert().values(
                    email=email, password_hash=password_hash, role="student"
                )
            )
            uid = result.inserted_primary_key[0]
    except IntegrityError:
        return fail("Email already registered.", 409)
    return jsonify(user_id=uid), 201


@api.post("/api/auth/login")
def login():
    email, password = credentials(body())
    limited = throttle(email)
    if limited:
        return limited
    with db().connect() as conn:
        row = (
            conn.execute(select(users).where(users.c.email == email)).mappings().first()
        )
    valid = check_password_hash(row["password_hash"] if row else _DUMMY_HASH, password)
    if row is None or not valid:
        return fail("Invalid email or password.", 401)
    # Revoke any existing session represented by this browser before replacing it.
    previous = session.get("auth_token")
    if previous:
        with db().begin() as conn:
            conn.execute(
                auth_sessions.delete().where(
                    auth_sessions.c.token_hash == digest(previous)
                )
            )
    issue_session(row["user_id"])
    return jsonify(user_id=row["user_id"], role=row["role"], csrf_token=csrf())


@api.post("/api/auth/logout")
def logout():
    with db().begin() as conn:
        conn.execute(
            auth_sessions.delete().where(
                auth_sessions.c.token_hash == digest(session["auth_token"])
            )
        )
    session.clear()
    return "", 204
