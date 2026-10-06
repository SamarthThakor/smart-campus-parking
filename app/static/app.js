let csrfToken = "";
const $ = id => document.getElementById(id);
async function request(path, method="GET", data) {
  const response = await fetch(path,{method,headers:{"Content-Type":"application/json","X-CSRF-Token":csrfToken},body:data===undefined?undefined:JSON.stringify(data)});
  const result = response.status===204?null:await response.json();
  if(!response.ok) throw new Error(result.error?.message || "Request failed.");
  return result;
}
function element(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
function report(error){$("message").textContent=error.message;}
async function refreshStudent(){
  const data=await request("/api/recommendations");const box=$("recommendation");box.replaceChildren();
  if(!data.recommendation){box.append(element("p",data.reason.replaceAll("_"," ")));}
  else {
    const r=data.recommendation;
    box.append(element("h3",r.name),element("p",r.available_spaces+" reported spaces · "+r.walking_minutes+"-minute walk · Permit accepted"),
      element("p","Next class: "+data.class_info.title+" at "+data.class_info.building_name),
      element("p","Be parked by "+new Date(r.parked_by).toLocaleString()),
      element("p","Availability updated "+new Date(r.updated_at).toLocaleString()));
    if(r.late_arrival_warning)box.append(element("p","The suggested parking time has passed. Allow extra time."));
  }
  const list=$("classes");list.replaceChildren();
  for(const c of await request("/api/classes"))list.append(element("li",["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][c.weekday]+" "+c.start_time.slice(0,5)+" — "+c.title));
}
async function refreshAdmin(){
  const panel=$("lots");panel.replaceChildren();
  for(const lot of await request("/api/admin/lots")){
    const form=element("form","");form.className="lot";form.append(element("h3",lot.name));
    const label=element("label","Spaces / "+lot.capacity);const count=element("input","");count.type="number";count.min=0;count.max=lot.capacity;count.value=lot.available_spaces;count.required=true;label.append(count);form.append(label);
    const statusLabel=element("label","Status");const select=element("select","");
    for(const state of ["open","closed"]){const option=element("option",state);option.value=state;select.append(option);}select.value=lot.status;statusLabel.append(select);form.append(statusLabel);
    const save=element("button","Save");form.append(save);
    form.onsubmit=async e=>{e.preventDefault();try{await request("/api/admin/lots/"+lot.lot_id,"PATCH",{available_spaces:Number(count.value),status:select.value});$("message").textContent=lot.name+" updated.";await refreshAdmin();}catch(error){report(error);}};
    panel.append(form);
  }
}
async function show(user){
  $("login-panel").hidden=true;$("dashboard").hidden=false;$("welcome").textContent=user.role==="admin"?"Parking administration":"Student dashboard";
  $("student").hidden=user.role!=="student";$("admin").hidden=user.role!=="admin";
  await (user.role==="admin"?refreshAdmin():refreshStudent());
}
$("login").onsubmit=async e=>{e.preventDefault();try{const values=Object.fromEntries(new FormData(e.target));const user=await request("/api/auth/login","POST",values);csrfToken=user.csrf_token;$("message").textContent="";await show(user);}catch(error){report(error);}};
$("refresh").onclick=()=>refreshStudent().catch(report);
$("logout").onclick=async()=>{try{await request("/api/auth/logout","POST",{});location.reload();}catch(error){report(error);}};
(async()=>{try{csrfToken=(await request("/api/auth/csrf")).csrf_token;const response=await fetch("/api/me");if(response.ok)await show(await response.json());}catch(error){report(error);}})();

