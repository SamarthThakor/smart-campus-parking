from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from .models import users, classes, lots, lot_permits, walks, buildings

def get_next_class(conn,user_id,now):
    if now.tzinfo is None:
        raise ValueError("now must include a time zone")
    rows=conn.execute(select(classes,buildings.c.name.label("building_name")).join(buildings,classes.c.building_id==buildings.c.building_id).where(classes.c.user_id==user_id)).mappings()
    upcoming=[]
    for row in rows:
        item=dict(row)
        day=now.date()+timedelta(days=(item["weekday"]-now.weekday())%7)
        occurrence=datetime.combine(day,item["start_time"],tzinfo=now.tzinfo)
        if occurrence<now:
            occurrence+=timedelta(days=7)
        item["starts_at"]=occurrence.isoformat()
        upcoming.append(item)
    return min(upcoming,key=lambda c:(c["starts_at"],c["class_id"])) if upcoming else None

def recommend_parking(conn,user_id,now):
    next_class=get_next_class(conn,user_id,now)
    result=dict(class_info=next_class,recommendation=None,alternatives=[],reason=None)
    if next_class is None:
        result["reason"]="no_upcoming_class"; return result
    permit_id=conn.execute(select(users.c.permit_id).where(users.c.user_id==user_id)).scalar()
    if permit_id is None:
        result["reason"]="permit_required"; return result
    query=select(lots,walks.c.walking_minutes).join(lot_permits,lots.c.lot_id==lot_permits.c.lot_id).join(walks,lots.c.lot_id==walks.c.lot_id).where(lot_permits.c.permit_id==permit_id,walks.c.building_id==next_class["building_id"],lots.c.status=="open",lots.c.available_spaces>0).order_by(walks.c.walking_minutes,lots.c.available_spaces.desc(),lots.c.lot_id)
    candidates=[]
    for record in conn.execute(query).mappings():
        lot=dict(record)
        parked_by=datetime.fromisoformat(next_class["starts_at"])-timedelta(minutes=lot["walking_minutes"]+5)
        lot.update(permit_eligible=True,parked_by=parked_by.isoformat(),late_arrival_warning=now>parked_by)
        candidates.append(lot)
    if candidates:
        result.update(recommendation=candidates[0],alternatives=candidates[1:3])
    else:
        result["reason"]="no_eligible_lot"
    return result

def update_lot(conn,lot_id,changes):
    current=conn.execute(select(lots).where(lots.c.lot_id==lot_id)).mappings().first()
    if current is None:
        raise LookupError("Lot not found.")
    if not changes or set(changes)-{"available_spaces","status"}:
        raise ValueError("Provide available_spaces and/or status.")
    spaces=changes.get("available_spaces",current["available_spaces"])
    status=changes.get("status",current["status"])
    if type(spaces) is not int or not 0<=spaces<=current["capacity"]:
        raise ValueError("Available spaces must be between zero and capacity.")
    if status not in {"open","closed"}:
        raise ValueError("Status must be open or closed.")
    conn.execute(lots.update().where(lots.c.lot_id==lot_id).values(available_spaces=spaces,status=status,updated_at=datetime.now(timezone.utc).isoformat()))
    return dict(conn.execute(select(lots).where(lots.c.lot_id==lot_id)).mappings().one())

