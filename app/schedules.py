from flask import current_app, g, jsonify, request, session
from sqlalchemy import select
from .http import api, body, db, fail, now
from .models import classes
from .validators import validated_class
from .services import get_next_class


@api.route("/api/classes", methods=["GET", "POST"])
def class_list():
    with db().begin() as conn:
        if request.method == "GET":
            return jsonify(
                [
                    dict(x)
                    for x in conn.execute(
                        select(classes).where(classes.c.user_id == g.user["user_id"])
                    ).mappings()
                ]
            )
        data = validated_class(body(), conn)
        result = conn.execute(
            classes.insert().values(user_id=g.user["user_id"], **data)
        )
        return jsonify(class_id=result.inserted_primary_key[0], **data), 201


@api.route("/api/classes/<int:cid>", methods=["PATCH", "DELETE"])
def class_detail(cid):
    with db().begin() as conn:
        condition = (classes.c.class_id == cid) & (
            classes.c.user_id == g.user["user_id"]
        )
        existing = conn.execute(select(classes).where(condition)).mappings().first()
        if existing is None:
            raise LookupError("Class not found.")
        if request.method == "DELETE":
            conn.execute(classes.delete().where(condition))
            return "", 204
        data = validated_class(body(), conn, existing)
        conn.execute(classes.update().where(condition).values(**data))
        return jsonify(class_id=cid, **data)


@api.get("/api/classes/next")
def next_class():
    with db().connect() as conn:
        return jsonify({"class": get_next_class(conn, g.user["user_id"], now())})
