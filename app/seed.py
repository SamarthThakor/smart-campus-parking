from datetime import datetime, time, timezone
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from .models import permits,users,buildings,classes,lots,lot_permits,walks
def seed_demo(conn):
    if conn.execute(select(users.c.user_id).limit(1)).first():
        raise ValueError("Seed requires an empty user table; existing data was not changed.")
    conn.execute(permits.insert(),[dict(permit_id=1,name="Student"),dict(permit_id=2,name="Staff")])
    pw=generate_password_hash("DemoParking123!")
    conn.execute(users.insert(),[dict(user_id=1,email="alex@example.test",password_hash=pw,role="student",permit_id=1),dict(user_id=2,email="jordan@example.test",password_hash=pw,role="admin",permit_id=None)])
    conn.execute(buildings.insert(),dict(building_id=1,name="Library Building",latitude=40.0,longitude=-74.0))
    conn.execute(classes.insert(),[dict(class_id=i+1,user_id=1,building_id=1,title="Software Engineering (demo)",weekday=i,start_time=time(10),end_time=time(11)) for i in range(7)])
    updated=datetime.now(timezone.utc).isoformat()
    conn.execute(lots.insert(),[dict(lot_id=i,name=n,capacity=c,available_spaces=a,status=s,latitude=40+i/1000,longitude=-74-i/1000,updated_at=updated) for i,n,c,a,s in [(1,"Lot A",60,10,"open"),(2,"Lot B",50,18,"open"),(3,"Lot C",40,20,"closed"),(4,"Staff Lot",20,10,"open")]])
    conn.execute(lot_permits.insert(),[dict(lot_id=i,permit_id=1 if i<4 else 2) for i in range(1,5)])
    conn.execute(walks.insert(),[dict(lot_id=i,building_id=1,walking_minutes=v) for i,v in [(1,8),(2,5),(3,2),(4,1)]])

