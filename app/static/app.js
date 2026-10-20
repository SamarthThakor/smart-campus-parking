let csrfToken = "", registration = false, editing = null, buildingNames = {}, campusZone = "America/New_York";
const $ = id => document.getElementById(id);
const days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
async function request(path, method="GET", data) {
  const response = await fetch(path,{method,headers:{"Content-Type":"application/json","X-CSRF-Token":csrfToken},body:data===undefined?undefined:JSON.stringify(data)});
  const result = response.status===204 ? null : await response.json();
  if(!response.ok) throw new Error(result.error?.message || "Request failed. Please try again.");
  return result;
}
function element(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
function message(text){$("message").textContent=text;}
function report(error){message(error.message);}
function dateTime(value){return new Date(value).toLocaleString("en-US",{timeZone:campusZone,weekday:"short",month:"short",day:"numeric",hour:"numeric",minute:"2-digit",timeZoneName:"short"});}
async function submit(form, action){
  const button=form.querySelector('button[type="submit"],button:not([type])');
  if(button) button.disabled=true;
  try {await action();} catch(error){report(error);} finally {if(button)button.disabled=false;}
}
function resetClassForm(){editing=null;$("class-form").reset();$("class-form-title").textContent="Add a class";$("class-save").textContent="Add class";$("cancel-edit").hidden=true;}
async function refreshStudent(){
  const [data,classes] = await Promise.all([request("/api/recommendations"),request("/api/classes")]);
  campusZone=data.campus_timezone;$("campus-time").textContent="Campus time zone: "+campusZone;
  const box=$("recommendation");box.replaceChildren();
  const reasons={no_upcoming_class:"Add a class below to get your parking recommendation.",permit_required:"Save your permit below to find eligible parking.",no_eligible_lot:"No suitable lot is available right now. Refresh later or contact campus parking."};
  if(!data.recommendation){box.append(element("h3","Your next parking plan"),element("p",reasons[data.reason]||"No recommendation available."));}
  else {
    const r=data.recommendation, tag=element("span","RECOMMENDED FOR YOUR NEXT CLASS");tag.className="tag";
    box.append(tag,element("h3",r.name));const metrics=element("p",r.available_spaces+" reported spaces | "+r.walking_minutes+"-minute walk");metrics.className="metrics";box.append(metrics);
    box.append(element("p",data.class_info.title+" | "+data.class_info.building_name+" | "+dateTime(data.class_info.starts_at)),element("p","Be parked by "+dateTime(r.parked_by)),element("p","Accepted permits: "+r.accepted_permits.join(", ")),element("p","Space count reported "+dateTime(r.updated_at)));
    if(data.provisional){const p=element("p","Future class: this plan is provisional. Current counts do not predict future availability; refresh before traveling.");p.className="warning";box.append(p);}
    if(r.late_arrival_warning)box.append(element("p","The suggested parking time has passed. Allow extra time."));
    if(data.alternatives.length)box.append(element("p","Other options: "+data.alternatives.map(a=>a.name+" ("+a.walking_minutes+" min, "+a.available_spaces+" spaces)").join("; ")));
  }
  const list=$("classes");list.replaceChildren();
  if(!classes.length)list.append(element("p","Your schedule is empty. Add your first class above."));
  for(const c of classes.sort((a,b)=>a.weekday-b.weekday||a.start_time.localeCompare(b.start_time))){
    const item=element("article","");item.className="schedule-item";
    const row=element("div","");row.className="row";const text=element("div","");text.append(element("strong",c.title),element("p",days[c.weekday]+" | "+c.start_time.slice(0,5)+"-"+c.end_time.slice(0,5)+" | "+buildingNames[c.building_id]));
    const actions=element("div","");actions.className="actions";const edit=element("button","Edit"),del=element("button","Delete");edit.className=del.className="secondary";
    edit.onclick=()=>{editing=c.class_id;for(const k of ["title","weekday","building_id","start_time","end_time"])$("class-form").elements[k].value=k.includes("time")?c[k].slice(0,5):c[k];$("class-form-title").textContent="Edit class";$("class-save").textContent="Save changes";$("cancel-edit").hidden=false;$("class-form").elements.title.focus();};
    del.onclick=async()=>{if(!confirm("Delete "+c.title+" from your schedule?"))return;del.disabled=true;try{await request("/api/classes/"+c.class_id,"DELETE");if(editing===c.class_id)resetClassForm();message("Class deleted.");await refreshStudent();}catch(e){report(e);del.disabled=false;}};
    actions.append(edit,del);row.append(text,actions);item.append(row);list.append(item);
  }
}
async function refreshAdmin(){
  const panel=$("lots");panel.replaceChildren();
  for(const lot of await request("/api/admin/lots")){
    const form=element("form","");form.className="card";form.setAttribute("aria-label",lot.name);form.append(element("h3",lot.name));
    const label=element("label","Reported spaces / "+lot.capacity);const count=element("input","");count.type="number";count.min=0;count.max=lot.capacity;count.value=lot.available_spaces;count.required=true;label.append(count);form.append(label);
    const statusLabel=element("label","Lot status"),select=element("select","");
    select.setAttribute("aria-label","Lot status");
    for(const state of ["open","closed"]){const option=element("option",state);option.value=state;select.append(option);}select.value=lot.status;statusLabel.append(select);form.append(statusLabel);
    form.append(element("button","Save lot"));const timestamp=element("p","Count reported: "+dateTime(lot.updated_at));timestamp.className="note";form.append(timestamp);
    form.onsubmit=e=>{e.preventDefault();submit(form,async()=>{const changes={status:select.value};if(Number(count.value)!==lot.available_spaces)changes.available_spaces=Number(count.value);await request("/api/admin/lots/"+lot.lot_id,"PATCH",changes);message(lot.name+" saved. Student recommendations now use this update.");await refreshAdmin();});};
    panel.append(form);
  }
}
async function show(){
  const user=await request("/api/me");$("login-panel").hidden=true;$("dashboard").hidden=false;$("account").textContent=user.email;$("welcome").textContent=user.role==="admin"?"Parking administration":"Your parking plan";
  $("student").hidden=user.role!=="student";$("admin").hidden=user.role!=="admin";
  if(user.role==="admin"){await refreshAdmin();return;}
  const [permits,buildings]=await Promise.all([request("/api/permits"),request("/api/buildings")]);
  $("permit").replaceChildren();const blank=element("option","Choose your permit");blank.value="";$("permit").append(blank);
  for(const p of permits){const option=element("option",p.name);option.value=p.permit_id;$("permit").append(option);}$("permit").value=user.permit_id||"";
  $("building").replaceChildren();for(const b of buildings){buildingNames[b.building_id]=b.name;const option=element("option",b.name);option.value=b.building_id;$("building").append(option);}
  await refreshStudent();
}
$("auth-switch").onclick=()=>{registration=!registration;$("auth-title").textContent=registration?"Create your account":"Welcome back";$("auth-help").textContent=registration?"Use at least 12 characters for your password.":"Sign in to see your schedule and parking options.";$("auth-submit").textContent=registration?"Create account":"Sign in";$("auth-switch").textContent=registration?"Already have an account? Sign in":"Create a student account";$("login").elements.password.minLength=registration?12:1;$("login").elements.password.autocomplete=registration?"new-password":"current-password";message("");};
$("login").onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{const data=Object.fromEntries(new FormData(e.target));if(registration)await request("/api/auth/register","POST",data);const user=await request("/api/auth/login","POST",data);csrfToken=user.csrf_token;message(registration?"Account created. Save your permit and add your first class.":"");await show();});};
$("permit-form").onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{await request("/api/me/permit","PATCH",{permit_id:Number($("permit").value)});message("Permit saved.");await refreshStudent();});};
$("class-form").onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{const data=Object.fromEntries(new FormData(e.target));data.weekday=Number(data.weekday);data.building_id=Number(data.building_id);await request(editing?"/api/classes/"+editing:"/api/classes",editing?"PATCH":"POST",data);resetClassForm();message("Class saved to your weekly schedule.");await refreshStudent();});};
$("cancel-edit").onclick=resetClassForm;
$("refresh").onclick=()=>refreshStudent().catch(report);
$("logout").onclick=async()=>{try{await request("/api/auth/logout","POST",{});location.reload();}catch(error){report(error);}};
(async()=>{try{csrfToken=(await request("/api/auth/csrf")).csrf_token;const response=await fetch("/api/me");if(response.ok)await show();}catch(error){report(error);}})();
