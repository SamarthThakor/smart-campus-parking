from flask import current_app, g, jsonify, request, session
from sqlalchemy import select
from .http import api, body, db, fail, now
import json
from datetime import datetime, timezone
from .models import lots, lot_permits, permits, lot_updates
from .services import recommend_parking, update_lot


@api.get("/api/recommendations")
def recommendation():
    with db().connect() as conn:
        return jsonify(recommend_parking(conn, g.user["user_id"], now()))


@api.get("/api/admin/lots")
def admin_lots():
    with db().connect() as conn:
        records = []
        for row in conn.execute(select(lots).order_by(lots.c.lot_id)).mappings():
            row = dict(row)
            row["permit_ids"] = list(
                conn.execute(
                    select(lot_permits.c.permit_id).where(
                        lot_permits.c.lot_id == row["lot_id"]
                    )
                ).scalars()
            )
            records.append(row)
        return jsonify(records)


@api.patch("/api/admin/lots/<int:lid>")
def lot_update(lid):
    changes = body()
    with db().begin() as conn:
        result = update_lot(conn, lid, changes)
        conn.execute(
            lot_updates.insert().values(
                lot_id=lid,
                actor_id=g.user["user_id"],
                changed_at=datetime.now(timezone.utc).isoformat(),
                changes_json=json.dumps(changes, sort_keys=True),
            )
        )
    return jsonify(result)


@api.put("/api/admin/lots/<int:lid>/permits")
def rules(lid):
    ids = body().get("permit_ids")
    if (
        not isinstance(ids, list)
        or any(type(i) is not int for i in ids)
        or len(ids) != len(set(ids))
    ):
        raise ValueError("Provide a list of unique permit IDs.")
    with db().begin() as conn:
        if (
            conn.execute(select(lots.c.lot_id).where(lots.c.lot_id == lid)).first()
            is None
        ):
            raise LookupError("Lot not found.")
        known = set(conn.execute(select(permits.c.permit_id)).scalars())
        if not set(ids) <= known:
            raise ValueError("Unknown permit ID.")
        conn.execute(lot_permits.delete().where(lot_permits.c.lot_id == lid))
        if ids:
            conn.execute(
                lot_permits.insert(), [dict(lot_id=lid, permit_id=i) for i in ids]
            )
        conn.execute(
            lot_updates.insert().values(
                lot_id=lid,
                actor_id=g.user["user_id"],
                changed_at=datetime.now(timezone.utc).isoformat(),
                changes_json=json.dumps({"permit_ids": ids}, sort_keys=True),
            )
        )
    return jsonify(permit_ids=ids)


@api.get("/api/admin/history")
def history():
    with db().connect() as conn:
        rows = conn.execute(
            select(lot_updates).order_by(lot_updates.c.update_id.desc()).limit(50)
        ).mappings()
        result = []
        for row in rows:
            item = dict(row)
            item["changes"] = json.loads(item.pop("changes_json"))
            result.append(item)
    return jsonify(result)
