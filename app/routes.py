import re
import secrets
from datetime import datetime,time
from zoneinfo import ZoneInfo
from flask import Blueprint,current_app,g,jsonify,render_template,request,session
from sqlalchemy import select,text
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash,generate_password_hash
from .models import users,permits,buildings,classes,lots,lot_permits
from .services import get_next_class,recommend_parking,update_lot
api=Blueprint("api",__name__)
def fail(message,status=400): return jsonify(error=dict(code=status,message=message)),status
def body():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): raise ValueError("A JSON object is required.")
    return data
def db(): return current_app.extensions["db"]
def now(): return current_app.config.get("NOW",lambda:datetime.now(ZoneInfo(current_app.config["CAMPUS_TIMEZONE"])))()
def csrf():
    if "csrf" not in session: session["csrf"]=secrets.token_hex(24)
    return session["csrf"]
@api.before_request
def protect():
    if not request.path.startswith("/api/"): return None
    if request.method in {"POST","PATCH","PUT","DELETE"}:
        expected=session.get("csrf")
        if not expected or not secrets.compare_digest(expected,request.headers.get("X-CSRF-Token","")): return fail("Missing or invalid CSRF token.",403)
    if request.path in {"/api/health","/api/auth/login","/api/auth/register","/api/auth/csrf"}: return None
    with db().connect() as conn: row=conn.execute(select(users).where(users.c.user_id==session.get("user_id"))).mappings().first()
    if row is None: return fail("Sign in first.",401)
    g.user=dict(row)
    if request.path.startswith("/api/admin/") and g.user["role"]!="admin": return fail("Administrator access required.",403)
@api.app_errorhandler(ValueError)
def invalid(error): return fail(str(error))
@api.app_errorhandler(LookupError)
def missing(error): return fail(str(error),404)
@api.app_errorhandler(SQLAlchemyError)
def database_error(error):
    current_app.logger.error("Database operation failed",exc_info=True)
    return fail("Database operation failed.",500)
@api.app_errorhandler(HTTPException)
def http_error(error): return fail(error.description,error.code)
@api.get("/")
def home(): return render_template("index.html")
@api.get("/api/auth/csrf")
def token(): return jsonify(csrf_token=csrf())
@api.get("/api/health")
def health():
    try:
        with db().connect() as conn: conn.execute(text("SELECT 1"))
    except SQLAlchemyError: return fail("Database unavailable.",503)
    return jsonify(status="ok")
@api.post("/api/auth/register")
def register():
    data=body(); email=data.get("email"); password=data.get("password")
    if not isinstance(email,str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email) or len(email)>255: raise ValueError("Enter a valid email address.")
    if not isinstance(password,str) or not 12<=len(password)<=128: raise ValueError("Password must contain 12 to 128 characters.")
    if set(data)-{"email","password"}: raise ValueError("Registration accepts only email and password.")
    try:
        with db().begin() as conn:
            result=conn.execute(users.insert().values(email=email.lower(),password_hash=generate_password_hash(password),role="student"))
            uid=result.inserted_primary_key[0]
    except IntegrityError: return fail("Email already registered.",409)
    return jsonify(user_id=uid),201
@api.post("/api/auth/login")
def login():
    data=body(); email=data.get("email"); password=data.get("password")
    if not isinstance(email,str) or not isinstance(password,str): raise ValueError("Email and password are required.")
    with db().connect() as conn: row=conn.execute(select(users).where(users.c.email==email.lower())).mappings().first()
    if row is None or not check_password_hash(row["password_hash"],password): return fail("Invalid email or password.",401)
    session.clear(); session["user_id"]=row["user_id"]
    return jsonify(user_id=row["user_id"],role=row["role"],csrf_token=csrf())
@api.post("/api/auth/logout")
def logout(): session.clear(); return "",204
@api.get("/api/me")
def me(): return jsonify(user_id=g.user["user_id"],email=g.user["email"],role=g.user["role"],permit_id=g.user["permit_id"])
@api.patch("/api/me/permit")
def permit():
    pid=body().get("permit_id")
    with db().begin() as conn:
        if type(pid) is not int or conn.execute(select(permits.c.permit_id).where(permits.c.permit_id==pid)).first() is None: raise ValueError("Choose a valid permit.")
        conn.execute(users.update().where(users.c.user_id==g.user["user_id"]).values(permit_id=pid))
    return jsonify(permit_id=pid)
@api.get("/api/buildings")
def building_list():
    with db().connect() as conn: return jsonify([dict(x) for x in conn.execute(select(buildings)).mappings()])
@api.get("/api/permits")
def permit_list():
    with db().connect() as conn: return jsonify([dict(x) for x in conn.execute(select(permits)).mappings()])
def validated_class(data,conn,existing=None):
    fields={"title","weekday","start_time","end_time","building_id"}
    if not data or set(data)-fields: raise ValueError("Provide valid class fields.")
    item={key:existing[key] for key in fields} if existing else {}; item.update(data)
    if set(item)!=fields or not isinstance(item["title"],str) or not item["title"].strip() or len(item["title"])>100: raise ValueError("All class fields and a title of 1 to 100 characters are required.")
    if type(item["weekday"]) is not int or not 0<=item["weekday"]<=6: raise ValueError("Weekday must be 0 to 6.")
    if type(item["building_id"]) is not int or conn.execute(select(buildings.c.building_id).where(buildings.c.building_id==item["building_id"])).first() is None: raise ValueError("Choose a valid building.")
    try:
        for key in ("start_time","end_time"):
            if isinstance(item[key],str):
                if not re.fullmatch(r"\d{2}:\d{2}",item[key]): raise ValueError()
                item[key]=time.fromisoformat(item[key])
            if not isinstance(item[key],time): raise ValueError()
        if item["end_time"]<=item["start_time"]: raise ValueError()
    except (ValueError,TypeError): raise ValueError("Use HH:MM times with end time after start time.")
    return item
@api.route("/api/classes",methods=["GET","POST"])
def class_list():
    with db().begin() as conn:
        if request.method=="GET": return jsonify([dict(x) for x in conn.execute(select(classes).where(classes.c.user_id==g.user["user_id"])).mappings()])
        data=validated_class(body(),conn); result=conn.execute(classes.insert().values(user_id=g.user["user_id"],**data))
        return jsonify(class_id=result.inserted_primary_key[0],**data),201
@api.route("/api/classes/<int:cid>",methods=["PATCH","DELETE"])
def class_detail(cid):
    with db().begin() as conn:
        condition=(classes.c.class_id==cid)&(classes.c.user_id==g.user["user_id"])
        existing=conn.execute(select(classes).where(condition)).mappings().first()
        if existing is None: raise LookupError("Class not found.")
        if request.method=="DELETE": conn.execute(classes.delete().where(condition)); return "",204
        data=validated_class(body(),conn,existing); conn.execute(classes.update().where(condition).values(**data))
        return jsonify(class_id=cid,**data)
@api.get("/api/classes/next")
def next_class():
    with db().connect() as conn: return jsonify({"class":get_next_class(conn,g.user["user_id"],now())})
@api.get("/api/recommendations")
def recommendation():
    with db().connect() as conn: return jsonify(recommend_parking(conn,g.user["user_id"],now()))
@api.get("/api/admin/lots")
def admin_lots():
    with db().connect() as conn:
        records=[]
        for row in conn.execute(select(lots).order_by(lots.c.lot_id)).mappings():
            row=dict(row); row["permit_ids"]=list(conn.execute(select(lot_permits.c.permit_id).where(lot_permits.c.lot_id==row["lot_id"])).scalars()); records.append(row)
        return jsonify(records)
@api.patch("/api/admin/lots/<int:lid>")
def lot_update(lid):
    with db().begin() as conn: result=update_lot(conn,lid,body())
    return jsonify(result)
@api.put("/api/admin/lots/<int:lid>/permits")
def rules(lid):
    ids=body().get("permit_ids")
    if not isinstance(ids,list) or any(type(i) is not int for i in ids) or len(ids)!=len(set(ids)): raise ValueError("Provide a list of unique permit IDs.")
    with db().begin() as conn:
        if conn.execute(select(lots.c.lot_id).where(lots.c.lot_id==lid)).first() is None: raise LookupError("Lot not found.")
        known=set(conn.execute(select(permits.c.permit_id)).scalars())
        if not set(ids)<=known: raise ValueError("Unknown permit ID.")
        conn.execute(lot_permits.delete().where(lot_permits.c.lot_id==lid))
        if ids: conn.execute(lot_permits.insert(),[dict(lot_id=lid,permit_id=i) for i in ids])
    return jsonify(permit_ids=ids)

