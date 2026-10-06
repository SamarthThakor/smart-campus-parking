"""Capture actual HTTP responses from the running local demo server."""
from urllib.request import build_opener, HTTPCookieProcessor, Request
from http.cookiejar import CookieJar
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
BASE=sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:5000"
def call(opener,path,method="GET",data=None,token=None):
    headers={"Content-Type":"application/json"}
    if token: headers["X-CSRF-Token"]=token
    req=Request(BASE+path,headers=headers,method=method,data=None if data is None else json.dumps(data).encode())
    with opener.open(req) as response:
        return response.status,json.load(response) if response.status!=204 else None
def sign_in(email):
    opener=build_opener(HTTPCookieProcessor(CookieJar()))
    _,csrf=call(opener,"/api/auth/csrf")
    _,result=call(opener,"/api/auth/login","POST",dict(email=email,password="DemoParking123!"),csrf["csrf_token"])
    return opener,result["csrf_token"]
student,_=sign_in("alex@example.test");admin,token=sign_in("jordan@example.test")
health=call(student,"/api/health");before=call(student,"/api/recommendations")
assert before[1]["recommendation"]["name"]=="Lot B"
try:
    update=call(admin,"/api/admin/lots/2","PATCH",{"status":"closed"},token)
    after=call(student,"/api/recommendations")
    assert update[0]==200 and after[1]["recommendation"]["name"]=="Lot A"
finally:
    call(admin,"/api/admin/lots/2","PATCH",{"status":"open"},token)
result={"captured_utc":datetime.now(timezone.utc).isoformat(),"base_url":BASE,
        "health":{"status":health[0],"body":health[1]},
        "before":{"status":before[0],"body":before[1]},
        "admin_update":{"status":update[0],"body":update[1]},
        "after":{"status":after[0],"body":after[1]},"restored":True}
out=Path(__file__).resolve().parents[1]/"docs"/"http-demo.json"
out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps({"health":health[0],"before":before[1]["recommendation"]["name"],
                 "admin_update":update[0],"after":after[1]["recommendation"]["name"],"restored":True},indent=2))

