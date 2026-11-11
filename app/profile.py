from flask import current_app, g, jsonify, request, session
from sqlalchemy import select
from .http import api, body, db, fail, now
from .models import users, permits, buildings
from .models import classes, auth_sessions
from werkzeug.security import check_password_hash
from .security import throttle


@api.get("/api/me")
def me():
    return jsonify(
        user_id=g.user["user_id"],
        email=g.user["email"],
        role=g.user["role"],
        permit_id=g.user["permit_id"],
    )


@api.patch("/api/me/permit")
def permit():
    pid = body().get("permit_id")
    with db().begin() as conn:
        if (
            type(pid) is not int
            or conn.execute(
                select(permits.c.permit_id).where(permits.c.permit_id == pid)
            ).first()
            is None
        ):
            raise ValueError("Choose a valid permit.")
        conn.execute(
            users.update()
            .where(users.c.user_id == g.user["user_id"])
            .values(permit_id=pid)
        )
    return jsonify(permit_id=pid)


@api.get("/api/me/export")
def export_data():
    with db().connect() as conn:
        schedule = [
            dict(row)
            for row in conn.execute(
                select(classes).where(classes.c.user_id == g.user["user_id"])
            ).mappings()
        ]
    response = jsonify(
        account={key: g.user[key] for key in ("user_id", "email", "role", "permit_id")},
        classes=schedule,
    )
    response.headers["Content-Disposition"] = (
        'attachment; filename="my-parking-data.json"'
    )
    return response


@api.delete("/api/me")
def delete_account():
    if g.user["role"] != "student":
        return fail("Administrator deletion requires an operator review.", 403)
    data = body()
    password = data.get("password")
    if (
        set(data) != {"password"}
        or not isinstance(password, str)
        or not 1 <= len(password) <= 128
    ):
        raise ValueError("Confirm your password.")
    limited = throttle(g.user["email"])
    if limited:
        return limited
    if not check_password_hash(g.user["password_hash"], password):
        return fail("Password confirmation failed.", 401)
    with db().begin() as conn:
        conn.execute(users.delete().where(users.c.user_id == g.user["user_id"]))
    session.clear()
    return "", 204


@api.get("/api/buildings")
def building_list():
    with db().connect() as conn:
        return jsonify([dict(x) for x in conn.execute(select(buildings)).mappings()])


@api.get("/api/permits")
def permit_list():
    with db().connect() as conn:
        return jsonify([dict(x) for x in conn.execute(select(permits)).mappings()])
