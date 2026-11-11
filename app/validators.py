"""Validate class inputs independently of HTTP routing."""

import re
from datetime import time
from sqlalchemy import select
from .models import buildings


def validated_class(data, conn, existing=None):
    fields = {"title", "weekday", "start_time", "end_time", "building_id"}
    if not data or set(data) - fields:
        raise ValueError("Provide valid class fields.")
    item = {key: existing[key] for key in fields} if existing else {}
    item.update(data)
    if (
        set(item) != fields
        or not isinstance(item["title"], str)
        or not item["title"].strip()
        or len(item["title"]) > 100
    ):
        raise ValueError(
            "All class fields and a title of 1 to 100 characters are required."
        )
    if type(item["weekday"]) is not int or not 0 <= item["weekday"] <= 6:
        raise ValueError("Weekday must be 0 to 6.")
    if (
        type(item["building_id"]) is not int
        or conn.execute(
            select(buildings.c.building_id).where(
                buildings.c.building_id == item["building_id"]
            )
        ).first()
        is None
    ):
        raise ValueError("Choose a valid building.")
    try:
        for key in ("start_time", "end_time"):
            if isinstance(item[key], str):
                if not re.fullmatch(r"\d{2}:\d{2}", item[key]):
                    raise ValueError()
                item[key] = time.fromisoformat(item[key])
            if not isinstance(item[key], time):
                raise ValueError()
        if item["end_time"] <= item["start_time"]:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Use HH:MM times with end time after start time.")
    return item
