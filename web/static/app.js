"use strict";
const $ = (id) => document.getElementById(id);
const el = (tag, cls, txt) => { const e=document.createElement(tag); if(cls)e.className=cls; if(txt!=null)e.textContent=txt; return e; };
const cap = (s) => (s||"").replace(/_/g," ").replace(/\b\w/g,m=>m.toUpperCase());
const RARITY = { common:"#b9c2cc", uncommon:"#4cd07d", rare:"#4ea3ff", very_rare:"#b069ff", legendary:"#ffac33", artifact:"#ff5d5d" };
// Installed add-ons: their scripts load before this one and push hook objects onto
// window.RPG_ADDONS -- creationFields(host,who,options), readCreation(form,host,who,options),
// sheetSection(section) -> html.
const ADDONS = window.RPG_ADDONS || [];

const S = {
  ws:null, connected:false,
  rulesets:[], settings:[], stories:[], storyDetail:null,
  sel:{ ruleset:null, setting:null, story:null },
  party:[], selectedPc:0,
  connection:null, backend:"…", llmConfigs:["default"],
  autoscroll:true, rules:{}, options:null,
  spellbook:{ casters:[], books:{}, selected:null, draft:null },
  equipment:{ member:null, view:null, inventory:[], msg:"" },
  shop:{ open:false, view:null, take:[], give:[], hl:{take:[],give:[]} },
};

// ---- WebSocket -------------------------------------------------------------
function connect(){
  const proto = location.protocol==="https:"?"wss":"ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`); S.ws=ws;
  // Clear the indicator on open rather than showing "connected": this is only the local web
  // server socket, and a "connected" label here misreads as the LLM model being connected (it
  // isn't until a backend is configured). Only surface connection *problems*.
  ws.onopen=()=>{ S.connected=true; setConn("",""); send({type:"catalog"}); send({type:"listSaves"}); };
  ws.onclose=()=>{ S.connected=false; setConn("disconnected — retrying…","bad"); setTimeout(connect,1500); };
  ws.onerror=()=>setConn("connection error","bad");
  ws.onmessage=(ev)=>{ try{ handle(JSON.parse(ev.data)); }catch(e){ console.error(e,ev.data); } };
}
function send(o){ if(S.ws&&S.connected) S.ws.send(JSON.stringify(o)); }
function setConn(t,cls){ const c=$("connState"); c.textContent=t; c.className="conn "+(cls||""); }

// ---- router ----------------------------------------------------------------
function handle(m){
  switch(m.type){
    case "catalog": S.rulesets=m.rulesets; S.settings=m.settings; S.stories=m.stories;
      S.connection=m.connection||S.connection; S.backend=m.backend||S.backend;
      renderRulesets(); applyLast(m.last); renderSettings(); renderStories(); renderConnBar(); send({type:"info"}); break;
    case "settings": S.settings=m.settings; S.stories=m.stories; renderSettings(); renderStories(); break;
    case "stories": S.stories=m.stories; renderStories(); break;
    case "storyDetail": if(m.story===S.sel.story){ S.storyDetail=m.detail; renderStoryDetail(); } break;
    case "info": renderInfo(m); renderLobbyRules(m); break;
    case "creationOptions": S.options=m.options; creatorRoster().forEach(w=>buildCharForm(w));
      if(!$("creator").classList.contains("hidden")) showCForm(currentWho()||"pc"); break;
    case "abilities": fillRolledAbilities(m.abilities); break;
    case "createError": flashCreator("Couldn’t create party: "+(m.error||""),true); break;
    case "began": case "loaded":
      if(m.type==="loaded"&&!m.ok){ flashSave("Load failed: "+(m.error||""),true); break; }
      S.party=m.party||[]; S.selectedPc=0; closeCreator(); enterGame(m); send({type:"spellbook"}); send({type:"getJournal"}); break;
    case "journal": onJournal(m.journal); break;
    case "party": S.party=m.party||[]; renderPortraits(); renderSheet(); break;
    case "spellbook": S.spellbook.casters=m.casters||[]; S.spellbook.books=m.books||{}; updateSpellbookTab(); break;
    case "spellAllocated": S.spellbook.books[m.member]=m.book;
      if(S.spellbook.selected===m.member){ S.spellbook.draft=null; renderSpellbook(); } send({type:"sheet"}); break;
    case "itemDetail": showDetail(itemDetailHtml(m.item)); break;
    case "equipment": S.equipment.member=m.member; S.equipment.view=m.view; S.equipment.inventory=m.inventory||[];
      renderEquipPortraits(); renderEquipScreen(); break;
    case "equipResult": if(!m.ok){ S.equipment.msg=m.message||"Can't equip that."; renderEquipScreen(); } break;
    case "restResult": S.equipment.msg=m.message||""; renderEquipScreen();
      if(m.longRest){ if(m.message) pushLog({style:"system",text:m.message}); send({type:"levelUp"}); } break;
    case "levelUp": onLevelUp(m); break;
    case "saves": renderSaves(m.saves||[]); fillLoadSelect(m.saves||[]); break;
    case "saved": if(m.ok){ flashSave(`Saved to “${m.slot}”.`); renderSaves(m.saves||[]); send({type:"listSaves"}); } else flashSave("Save failed: "+(m.error||""),true); break;
    case "ruleSet": syncOptionalToggle(m.key,m.on); break;
    case "event": onEvent(m); break;
    case "ready": hideThinking(); break;
    case "ended": chatEnd("— the session has ended —"); break;
    case "error": pushLog({style:"crit-fail", text:"[error] "+(m.error||"")}); break;
    case "log": pushLog({style:m.style||m.cat||"muted", text:m.text||""}); break;
    case "shop": if(!m.view){ pushLog({style:"system",text:"No merchant to trade with here."}); break; }
      S.shop.open=true; S.shop.view=m.view; renderTradePanel(); break;
    case "shopClosed": S.shop.open=false; S.shop.take=[]; S.shop.give=[]; closeTradePanel(); break;
    case "shopError": pushLog({style:"system", text:m.error||"Can't open a shop."}); break;
    case "dealResult": onDealResult(m); break;
    case "llamaSettings": renderLlm(m); break;
    case "llamaSettingsSaved": onLlamaSaved(m); break;
    case "llmConfigs": onLlmConfigs(m); break;
    case "llmConfigSaved": onLlmConfigSaved(m); break;
    case "connectionSaved": onConnectionSaved(m); break;
    case "connectionTest": onConnectionTest(m); break;
  }
}

// ===== LOBBY ================================================================
function optCard(item,sel,dis){
  const c=el("button","opt-card"+(sel?" sel":"")+(dis?" disabled":""));
  c.appendChild(el("div","nm",item.name)); if(item.blurb) c.appendChild(el("div","bl",item.blurb));
  const meta=[]; if(item.version)meta.push("v"+item.version); if(item.status)meta.push(item.status);
  if(item.tone)meta.push(item.tone); if(item.wired===false)meta.push("preview");
  if(meta.length) c.appendChild(el("div","meta",meta.join(" · "))); return c;
}
// group a list of {category} items into [{cat, label, items}], preserving a fixed category order
function groupBy(items,order){
  const seen={}; const groups=[];
  const push=(cat,label,it)=>{ let g=seen[cat]; if(!g){ g=seen[cat]={cat,label,items:[]}; groups.push(g);} g.items.push(it); };
  (order||[]).forEach(([cat,label])=>{ items.filter(x=>(x.category||"")===cat).forEach(it=>push(cat,label,it)); });
  items.filter(x=>!(order||[]).some(([c])=>c===(x.category||""))).forEach(it=>push(it.category||"other",cap(it.category||"Other"),it));
  return groups;
}
function renderGrouped(box,groups,isSel,onPick){
  box.innerHTML="";
  groups.forEach(g=>{
    if(g.label) box.appendChild(el("div","group-h",g.label));
    g.items.forEach(it=>{ const c=optCard(it,isSel(it),it.disabled);
      c.onclick=()=>{ if(it.disabled)return; onPick(it); }; box.appendChild(c); });
  });
}
const RULE_CATS=[["d20 / D&D-based","d20 / D&D-based"],["Storyteller (revised)","Storyteller (revised)"]];
const STORY_CATS=[["adventure","Adventures"],["free","Free Exploration"],["test","Test scenes"]];
function renderRulesets(){
  const groups=groupBy(S.rulesets.map(r=>({...r,disabled:!r.wired&&r.key!=="dnd"})),RULE_CATS);
  renderGrouped($("list-rulesets"),groups,r=>S.sel.ruleset===r.key,r=>{
    S.sel.ruleset=r.key; S.sel.setting=null; S.sel.story=null; S.storyDetail=null;
    renderRulesets(); renderStoryDetail(); send({type:"settings",ruleset:r.key}); updateFoot(); });
}
function renderSettings(){ const box=$("list-settings"); box.innerHTML="";
  if(!S.sel.ruleset){ box.appendChild(el("div","bl","Choose a ruleset first.")); return; }
  S.settings.forEach(s=>{ const c=optCard(s,S.sel.setting===s.key);
    c.onclick=()=>{ S.sel.setting=s.key; S.sel.story=null; S.storyDetail=null; renderSettings(); renderStoryDetail();
      send({type:"stories",ruleset:S.sel.ruleset,setting:s.key}); updateFoot(); }; box.appendChild(c); });
  if(S.settings.length&&!S.sel.setting){ S.sel.setting=S.settings[0].key; renderSettings();
    send({type:"stories",ruleset:S.sel.ruleset,setting:S.sel.setting}); } }
function renderStories(){ const box=$("list-stories");
  if(!S.sel.setting){ box.innerHTML=""; box.appendChild(el("div","bl","Choose a world first.")); return; }
  renderGrouped(box,groupBy(S.stories,STORY_CATS),s=>S.sel.story===s.key,s=>{
    S.sel.story=s.key; renderStories(); updateFoot(); requestStoryDetail(); });
}
function selectedStory(){ return S.stories.find(s=>s.key===S.sel.story)||null; }
function requestStoryDetail(){ S.storyDetail=null; renderStoryDetail();
  if(S.sel.ruleset&&S.sel.setting&&S.sel.story)
    send({type:"storyDetail",ruleset:S.sel.ruleset,setting:S.sel.setting,story:S.sel.story}); }
function applyLast(last){ if(!last)return;
  if(S.rulesets.some(r=>r.key===last.ruleset)) S.sel.ruleset=last.ruleset;
  S.sel.setting=last.setting||null; S.sel.story=last.story||null; renderRulesets(); updateFoot();
  if(S.sel.story) requestStoryDetail(); else renderStoryDetail(); }
function updateFoot(){ const ok=S.sel.ruleset&&S.sel.setting;
  const nm=(arr,k)=>(arr.find(x=>x.key===k)||{}).name||"…";
  $("lobby-summary").textContent= ok ? `${nm(S.rulesets,S.sel.ruleset)} · ${nm(S.settings,S.sel.setting)}${S.sel.story?` · ${nm(S.stories,S.sel.story)}`:""}` : "Pick a ruleset and world.";
  // a campaign ships with a ready pregen party ("Begin adventure", primary) but can also be played
  // with a party you build ("Custom party"). Free/test picks: "Create a party" is the primary action.
  const st=selectedStory(); const campaign=!!(st&&st.campaign);
  const create=$("createBtn"), begin=$("beginPregenBtn");
  create.classList.remove("hidden"); create.disabled=!ok;
  create.textContent=campaign?"Custom party":"Create a party";
  create.title=campaign?"Build your own party and play this adventure with it":"Build a party for free exploration";
  create.classList.toggle("primary",!campaign); create.classList.toggle("ghost",campaign);
  begin.disabled=!(ok&&S.sel.story);
  begin.classList.toggle("primary",campaign); begin.classList.toggle("ghost",!campaign);
  begin.textContent=campaign?"Begin adventure":"Quick start";
}
// ---- story detail panel (chapter roadmap + counts + party) -----------------
function renderStoryDetail(){
  const host=$("storyDetail"); if(!host) return; host.innerHTML="";
  if(!S.sel.story){ host.appendChild(el("div","sd-empty","Pick a story to see its details.")); return; }
  const d=S.storyDetail;
  if(!d){ host.appendChild(el("div","sd-empty","Loading…")); return; }
  host.appendChild(el("div","sd-title",d.name||cap(S.sel.story)));
  const kindLabel={adventure:"Full adventure",free:"Free exploration",test:"Test scene"}[d.kind]||"";
  if(kindLabel){ const k=el("div","sd-kind"); k.appendChild(el("span","sd-kind-badge sd-"+(d.kind||"other"),kindLabel));
    if(d.tone) k.appendChild(el("span","sd-tone",d.tone)); host.appendChild(k); }
  if(d.description) host.appendChild(el("p","sd-desc",d.description));
  if(d.chapters&&d.chapters.length) host.appendChild(chapterGraph(d.chapters));
  if(d.stats&&d.stats.length){ const box=el("div","sd-stats");
    d.stats.forEach(s=>{ const c=el("div","sd-stat"); c.appendChild(el("div","sd-stat-v",String(s.value)));
      c.appendChild(el("div","sd-stat-l",s.label)); box.appendChild(c); }); host.appendChild(box); }
  if(d.party&&d.party.length){ host.appendChild(el("div","sd-h","Your party"));
    const pl=el("div","sd-party");
    d.party.forEach(p=>{ const row=el("div","sd-pc");
      row.appendChild(el("span","sd-pc-nm",p.name));
      row.appendChild(el("span","sd-pc-sub",`${cap(p.race)} ${cap(p.klass)} ${p.level}`.trim()));
      pl.appendChild(row); }); host.appendChild(pl); }
}
// a horizontal chapter roadmap: implemented chapters glow blue, the rest are dim placeholders.
function chapterGraph(chapters){
  const wrap=el("div","chap-graph");
  wrap.appendChild(el("div","sd-h","Chapters"));
  const track=el("div","chap-track");
  chapters.forEach((c,i)=>{
    const node=el("div","chap-node"+(c.implemented?" done":""));
    if(i>0) node.classList.add("linked");
    const dot=el("div","chap-dot"); dot.textContent=c.n!=null?c.n:(i+1);
    node.appendChild(dot);
    node.appendChild(el("div","chap-lbl",c.title||("Ch. "+(c.n||i+1))));
    node.title=`Chapter ${c.n||i+1}: ${c.title||""}`+(c.implemented?" (implemented)":" (not yet implemented)");
    track.appendChild(node);
  });
  wrap.appendChild(track);
  const done=chapters.filter(c=>c.implemented).length;
  wrap.appendChild(el("div","chap-legend",`● ${done} implemented · ○ ${chapters.length-done} planned`));
  return wrap;
}

function renderLobbyRules(m){
  const rl=$("lobbyRules"); rl.innerHTML=""; (m.rules||[]).forEach(r=>rl.appendChild(el("li",null,r.name)));
  const ol=$("lobbyOptional"); ol.innerHTML="";
  (m.optional||[]).forEach(o=>{ const row=el("label","opt mini-opt"); const left=el("span");
    left.appendChild(el("span",null,o.name)); left.appendChild(el("span","badge",o.implemented?"ready":"planned"));
    const cb=el("input"); cb.type="checkbox"; cb.dataset.key=o.key; cb.checked=(o.key in S.rules)?S.rules[o.key]:!!o.on; cb.disabled=!o.implemented;
    cb.onchange=()=>{ S.rules[o.key]=cb.checked; if(S.sel.ruleset) send({type:"creationOptions",ruleset:S.sel.ruleset,rules:S.rules}); };
    row.appendChild(left); row.appendChild(cb); ol.appendChild(row); }); }
function syncOptionalToggle(k,on){ document.querySelectorAll(`#lobbyOptional input[data-key="${k}"]`).forEach(cb=>cb.checked=on); }
function fillLoadSelect(saves){ const sel=$("loadSelect"); sel.innerHTML="";
  if(!saves.length){ sel.appendChild(el("option",null,"No saves yet")); sel.disabled=true; $("loadBtn").disabled=true; return; }
  saves.forEach(s=>{ const o=el("option",null,`${s.pc_name||"?"} — ${s.slot}`); o.value=s.slot; sel.appendChild(o); });
  sel.disabled=false; $("loadBtn").disabled=false; }
$("loadBtn").onclick=()=>{ const slot=$("loadSelect").value; if(slot) send({type:"load",slot}); };
$("beginPregenBtn").onclick=()=>{ if(S.sel.ruleset&&S.sel.setting) send({type:"begin",ruleset:S.sel.ruleset,setting:S.sel.setting,story:S.sel.story||"__free__"}); };
$("createBtn").onclick=()=>openCreator();

// ===== CREATION WIZARD ======================================================
// The party is a roster: the PC plus any number of optional allies (unique ids a1, a2, …). When an
// authored campaign is selected the created party plays THAT adventure; otherwise it's free play.
const ALLY_CAP=5;
let _allyCounter=0;
function creatorRoster(){ return ["pc"].concat((S.creator&&S.creator.allies)||[]); }
function whoLabel(who){ if(who==="pc") return "Player character"; return "Ally "+creatorRoster().indexOf(who); }
function currentWho(){ const t=document.querySelector("#creatorTabs .ctab.active"); return t?t.dataset.who:null; }
function openCreator(){ if(!S.sel.ruleset)return;
  S.creator={ allies:["a"+(++_allyCounter)] };            // start with one optional ally slot
  $("charForms").innerHTML="";
  const story=selectedStory(); const campaign=!!(story&&story.campaign);
  $("creatorTitle").textContent = campaign ? ("Create a party — "+(story.name||"adventure")) : "Create your party";
  $("startPartyBtn").textContent = campaign ? "Begin adventure" : "Begin exploration";
  renderCreatorTabs("pc");
  send({type:"creationOptions",ruleset:S.sel.ruleset,rules:S.rules});
  $("creator").classList.remove("hidden"); }
function closeCreator(){ $("creator").classList.add("hidden"); }
$("creatorClose").onclick=closeCreator;
function renderCreatorTabs(active){
  const tabs=$("creatorTabs"); active=active||currentWho()||"pc"; tabs.innerHTML="";
  creatorRoster().forEach(who=>{
    const b=el("button","ctab"+(who===active?" active":"")); b.dataset.who=who;
    b.appendChild(document.createTextNode(whoLabel(who)));
    if(who!=="pc"){ const x=el("span","ctab-x","✕"); x.title="Remove this ally";
      x.onclick=(e)=>{ e.stopPropagation(); removeAlly(who); }; b.appendChild(x); }
    b.onclick=()=>showCForm(who); tabs.appendChild(b);
  });
  if((S.creator.allies||[]).length<ALLY_CAP){
    const add=el("button","ctab ctab-add","＋ Add ally"); add.onclick=addAlly; tabs.appendChild(add); }
}
function addAlly(){ const who="a"+(++_allyCounter); S.creator.allies.push(who);
  buildCharForm(who); renderCreatorTabs(who); showCForm(who); }
function removeAlly(who){ S.creator.allies=(S.creator.allies||[]).filter(w=>w!==who);
  const f=$("form-"+who); if(f) f.remove(); renderCreatorTabs("pc"); showCForm("pc"); }
function showCForm(who){ document.querySelectorAll("#creatorTabs .ctab").forEach(t=>t.classList.toggle("active",t.dataset.who===who));
  document.querySelectorAll("#charForms .char-form").forEach(f=>f.classList.toggle("hidden",f.id!=="form-"+who)); }

function selField(label,opts,id,cur){ const w=el("label","field"); w.appendChild(el("span","fl",label));
  const s=el("select"); s.id=id; opts.forEach(o=>{ const k=o.key!=null?o.key:o; const op=el("option",null,o.name||cap(k)); op.value=k; if(k===cur)op.selected=true; s.appendChild(op); });
  w.appendChild(s); return w; }
function textField(label,id,ph,val){ const w=el("label","field"); w.appendChild(el("span","fl",label));
  const i=el("input"); i.id=id; i.type="text"; if(ph)i.placeholder=ph; if(val)i.value=val; w.appendChild(i); return w; }
function multiField(label,opts,name,cls){ const w=el("div","field"); w.appendChild(el("span","fl",label));
  const box=el("div","chips-pick"+(cls?(" "+cls):""));
  opts.forEach(o=>{ const k=o.key!=null?o.key:o; const b=el("button","chip-toggle"); b.type="button"; b.textContent=o.label||cap(k);
    b.dataset.name=name; b.dataset.val=k; b.onclick=()=>b.classList.toggle("on"); box.appendChild(b); });
  w.appendChild(box); return w; }
function multiValues(host,name){ return Array.from(host.querySelectorAll(`.chip-toggle.on[data-name="${name}"]`)).map(b=>b.dataset.val); }

function buildCharForm(who){
  const opt=S.options; if(!opt)return;
  let host=$("form-"+who);
  if(!host){ host=el("div","char-form hidden"); host.id="form-"+who; $("charForms").appendChild(host); }
  host.innerHTML="";
  const pw=el("label","field"); pw.appendChild(el("span","fl","Pre-generated"));
  const ps=el("select"); ps.id=`pregen-${who}`;
  ps.appendChild(Object.assign(el("option",null,who!=="pc"?"— none / build from scratch —":"— build from scratch —"),{value:""}));
  (opt.pregens||[]).forEach(p=>{ if(who!=="pc"||p.role!=="ally"){ const o=el("option",null,`${p.name} — ${p.race} ${p.klass}`); o.value=p.key; ps.appendChild(o);} });
  ps.onchange=()=>host.querySelector(".build-fields").classList.toggle("hidden",!!ps.value);
  pw.appendChild(ps); host.appendChild(pw);
  const fields=el("div","build-fields"); host.appendChild(fields);
  // Two columns on wide screens: identity on the left, ability scores + skills on the right.
  const cols=el("div","cform-cols"); fields.appendChild(cols);
  const left=el("div","cform-col"), right=el("div","cform-col");
  cols.appendChild(left); cols.appendChild(right);
  left.appendChild(textField("Name",`name-${who}`,who!=="pc"?"Ally name":"Character name",""));
  const grid=el("div","field-grid"); left.appendChild(grid);
  grid.appendChild(selField("Race",opt.races,`race-${who}`));
  grid.appendChild(selField("Class",opt.classes,`class-${who}`));
  grid.appendChild(selField("Background",opt.backgrounds,`bg-${who}`));
  grid.appendChild(selField("Alignment",opt.alignments.map(a=>({key:a.key,name:a.label+(a.note?` (${a.note})`:"")})),`align-${who}`));
  const genders=(opt.genders||["male","female","androgynous","non_applicable"]).map(g=>({key:g,name:cap(g)}));
  grid.appendChild(selField("Gender",genders,`gender-${who}`));
  right.appendChild(buildAbilityControl(who));
  const sw=el("div","field"); sw.id=`skills-wrap-${who}`; right.appendChild(sw);
  $(`class-${who}`).addEventListener("change",()=>renderSkillPicker(who)); renderSkillPicker(who);
  ADDONS.forEach(x=>x.creationFields&&x.creationFields(fields,who,opt)); }

function buildAbilityControl(who){
  const opt=S.options, pb=opt.point_buy; const abils=pb.abilities;
  const wrap=el("div","field ability-ctl"); wrap.appendChild(el("span","fl","Ability scores"));
  const modes=el("div","mode-row"); ["pointbuy","array","roll"].forEach(mode=>{
    const b=el("button","mode-btn"+(mode==="pointbuy"?" on":"")); b.type="button"; b.dataset.mode=mode;
    b.textContent={pointbuy:"Point buy",array:"Standard array",roll:"Roll 4d6"}[mode];
    b.onclick=()=>{ wrap.querySelectorAll(".mode-btn").forEach(x=>x.classList.remove("on")); b.classList.add("on"); wrap.dataset.mode=mode;
      if(mode==="array") applyArray(who); if(mode==="roll") send({type:"rollAbilities",abilities:S.options.point_buy.abilities}); updateBudget(who); };
    modes.appendChild(b); }); wrap.appendChild(modes); wrap.dataset.mode="pointbuy";
  const rows=el("div","abil-rows");
  const START=8, m0=Math.floor((START-10)/2);   // modifier for the starting score, computed (not "+0")
  abils.forEach(a=>{ const r=el("div","abil-row"); r.appendChild(el("span","an",a.toUpperCase()));
    const minus=el("button","step"); minus.type="button"; minus.textContent="−";
    const val=el("span","av"); val.id=`abil-${who}-${a}`; val.textContent=String(START); val.dataset.v=String(START);
    const plus=el("button","step"); plus.type="button"; plus.textContent="+";
    minus.onclick=()=>stepAbil(who,a,-1); plus.onclick=()=>stepAbil(who,a,1);
    r.appendChild(minus); r.appendChild(val); r.appendChild(plus);
    // Initialise the modifier from the score deterministically, so it doesn't flicker
    // (e.g. show +0 for a score of 8 until the row is first touched, then jump to -1).
    const mod=el("span","amod"); mod.id=`mod-${who}-${a}`; mod.textContent=(m0>=0?"+":"")+m0; r.appendChild(mod); rows.appendChild(r); });
  wrap.appendChild(rows);
  const bud=el("div","budget"); bud.id=`budget-${who}`; wrap.appendChild(bud);
  setTimeout(()=>updateBudget(who),0); return wrap; }

const PB_COST={8:0,9:1,10:2,11:3,12:4,13:5,14:7,15:9};
function abilVal(who,a){ const e=$(`abil-${who}-${a}`); return e?parseInt(e.dataset.v):10; }
function setAbil(who,a,v){ const e=$(`abil-${who}-${a}`); if(!e)return; v=Math.max(3,Math.min(18,v)); e.dataset.v=v; e.textContent=v;
  const md=Math.floor((v-10)/2); $(`mod-${who}-${a}`).textContent=(md>=0?"+":"")+md; }
function stepAbil(who,a,d){ const mode=$(`budget-${who}`).closest(".ability-ctl").dataset.mode;
  let v=abilVal(who,a)+d;
  if(mode==="pointbuy"){ v=Math.max(8,Math.min(15,v)); const trial={...currentScores(who),[a]:v};
    if(d>0 && pbSpent(trial)>S.options.point_buy.budget) return; }
  setAbil(who,a,v); updateBudget(who); }
function currentScores(who){ const o={}; S.options.point_buy.abilities.forEach(a=>o[a]=abilVal(who,a)); return o; }
function pbSpent(scores){ let t=0; for(const v of Object.values(scores)){ if(v<8||v>15) return 9999; t+=PB_COST[v]||0; } return t; }
function updateBudget(who){ const ctl=$(`budget-${who}`).closest(".ability-ctl"); const mode=ctl.dataset.mode; const b=$(`budget-${who}`);
  if(mode==="pointbuy"){ const spent=pbSpent(currentScores(who)); const bud=S.options.point_buy.budget;
    b.textContent=`Points: ${spent} / ${bud}`; b.classList.toggle("over",spent>bud); }
  else b.textContent=mode==="array"?"Standard array assigned (you may still adjust).":"Rolled 4d6 (drop lowest)."; }
function applyArray(who){ const arr=(S.options.point_buy.standard_array||[]).slice(); const abils=S.options.point_buy.abilities;
  abils.forEach((a,i)=>setAbil(who,a,arr[i]!=null?arr[i]:10)); }
function fillRolledAbilities(scores){ creatorRoster().forEach(who=>{ if(!$(`abil-${who}-str`))return;
    Object.entries(scores).forEach(([a,v])=>{ if($(`abil-${who}-${a}`)) setAbil(who,a,v); });
    const ctl=$(`abil-${who}-str`).closest(".ability-ctl"); if(ctl&&ctl.dataset.mode==="roll") updateBudget(who); }); }

function renderSkillPicker(who){
  const opt=S.options; const ck=$(`class-${who}`).value; const cls=opt.classes.find(c=>c.key===ck)||{};
  const list=cls.skill_list||[]; const n=cls.skill_choices||2; const wrap=$(`skills-wrap-${who}`); wrap.innerHTML="";
  wrap.appendChild(el("span","fl",`Skill proficiencies (choose ${n})`));
  const box=el("div","chips-pick");
  list.forEach(sk=>{ const b=el("button","chip-toggle"); b.type="button"; b.textContent=cap(sk); b.dataset.name=`skill-${who}`; b.dataset.val=sk;
    b.onclick=()=>{ const on=box.querySelectorAll(".chip-toggle.on").length; if(!b.classList.contains("on")&&on>=n) return; b.classList.toggle("on"); };
    box.appendChild(b); });
  wrap.appendChild(box); }

function readSpec(who){
  const pg=$(`pregen-${who}`).value; if(pg) return {pregen:pg};
  const ab={}; ["str","dex","con","int","wis","cha"].forEach(a=>ab[a]=abilVal(who,a));
  const host=$("form-"+who);
  const form={ name:$(`name-${who}`).value.trim()||(who!=="pc"?"Companion":"Adventurer"),
    race:$(`race-${who}`).value, class:$(`class-${who}`).value, background:$(`bg-${who}`).value,
    alignment:$(`align-${who}`).value, gender:$(`gender-${who}`).value,
    abilities:ab, skills:multiValues(host,`skill-${who}`) };
  ADDONS.forEach(x=>x.readCreation&&x.readCreation(form,host,who,S.options));
  return {form};
}
function allyRequested(who){ const pg=$("pregen-"+who), nm=$("name-"+who);
  return !!(pg&&pg.value) || !!(nm && nm.value.trim()!==""); }
$("startPartyBtn").onclick=()=>{
  if(!S.options){ return; }
  const allies=[]; (S.creator.allies||[]).forEach(who=>{ if($("form-"+who)&&allyRequested(who)) allies.push(readSpec(who)); });
  const msg={ type:"createParty", ruleset:S.sel.ruleset, setting:S.sel.setting,
              story:S.sel.story||"__free__", rules:S.rules, pc:readSpec("pc"), allies };
  flashCreator("Summoning your party…"); send(msg);
};
function flashCreator(t,bad){ const m=$("creatorMsg"); m.textContent=t; m.style.color=bad?"var(--bad)":"var(--good)"; }

// ===== GAME shell ===========================================================
function enterGame(m){
  $("lobby").classList.add("hidden"); $("creator").classList.add("hidden"); $("game").classList.remove("hidden");
  $("chat").innerHTML=""; $("log").innerHTML=""; hideThinking();   // fresh session: clear last game's chat + log
  const v=m.versions||{}; const capn=(v.story&&v.story.name)||(v.setting&&v.setting.name)||"Your tale"; $("sceneCap").textContent=capn;
  if(S.party[0]&&S.party[0].decoration) $("sceneSigil").textContent=S.party[0].decoration.align_sigil||"❖";
  showTab("play"); renderPortraits(); renderSheet(); send({type:"levelUp"}); $("cmd").focus();
}
function showTab(name){
  document.querySelectorAll(".rail .tab").forEach(t=>t.classList.toggle("active",t.dataset.tab===name));
  document.querySelectorAll(".view").forEach(vw=>vw.classList.toggle("active",vw.id==="view-"+name));
  if(name==="info") send({type:"info"}); if(name==="saves") send({type:"listSaves"});
  if(name==="character") send({type:"sheet"}); if(name==="spellbook"){ send({type:"spellbook"}); }
  if(name==="equipment"){ S.equipment.msg=""; send({type:"equipment", member:currentMemberName()}); }
  if(name==="levelup") send({type:"levelUp"});
  if(name==="journal") send({type:"getJournal"});
  if(name==="llm"){ send({type:"getLlamaSettings"}); send({type:"listLlmConfigs"}); }
}
function currentMemberName(){ return (S.party[S.selectedPc]||{}).name || ""; }
document.querySelectorAll(".rail .tab").forEach(t=>{ if(t.dataset.tab) t.onclick=()=>showTab(t.dataset.tab); });
$("railToggle").onclick=()=>$("game").classList.toggle("rail-collapsed");
$("toLobby").onclick=()=>{ $("game").classList.add("hidden"); $("lobby").classList.remove("hidden"); send({type:"listSaves"}); };

// ===== PLAY =================================================================
function onEvent(m){
  if(m.kind==="narration"){ hideThinking(); chatSay(m.text); if(m.story) send({type:"getJournal"}); }
  else if(m.kind==="session_end"){ hideThinking(); chatEnd(m.text); }
  else if(m.kind==="menu"){ hideThinking(); showMenu(m); }
  else if(m.kind==="story"){ pushLog(m); send({type:"getJournal"}); }   // story beat -> refresh Journal
  else { if(m.cat==="error") hideThinking(); pushLog(m); }
}
function onJournal(j){
  S.journal=j||{}; updateJournalTab();
  if(document.querySelector("#view-journal.active")) renderJournal();
}
function updateJournalTab(){
  const tab=$("tab-journal"); if(!tab) return;
  const j=S.journal||{};
  tab.classList.toggle("hidden", !(j.chapter || (j.objectives||[]).length || (j.npc_tasks||[]).length));
}
function renderJournal(){
  const j=S.journal||{}, host=$("journalBody"); if(!host) return; host.innerHTML="";
  if(!j.chapter && !(j.objectives||[]).length){ host.appendChild(el("div","jr-empty","No active story.")); return; }
  if(j.adventure) host.appendChild(el("div","jr-adv",j.adventure));
  host.appendChild(el("div","jr-chapter",j.chapter||""));
  const sec=el("div","jr-section"); sec.appendChild(el("div","jr-h","Objectives"));
  const list=el("div","jr-list");
  (j.objectives||[]).forEach(o=>{
    const bad=(o.state==="fail"||o.state==="partial_fail");
    const done=o.done && !bad;
    const row=el("div","jr-obj"+(done?" done":"")+(bad?" bad":""));
    row.appendChild(el("span","jr-mark", o.state==="open"?"○":(bad?"✗":"✓")));
    const extra=(o.state && o.state!=="open" && o.state!=="full" && o.state!=="done")?` (${o.state})`:"";
    row.appendChild(el("span","jr-text", (o.text||"")+extra));
    list.appendChild(row);
  });
  if(!(j.objectives||[]).length) list.appendChild(el("div","jr-obj","— none yet —"));
  sec.appendChild(list); host.appendChild(sec);
  if((j.npc_tasks||[]).length){
    const ns=el("div","jr-section"); ns.appendChild(el("div","jr-h","In the shadows"));
    (j.npc_tasks||[]).forEach(nt=>{
      const row=el("div","jr-npc"+(nt.done?" done":""));
      row.appendChild(el("span","jr-text", nt.summary||nt.key));
      row.appendChild(el("span","jr-prog", nt.done?"complete":`${nt.phase}/${nt.total}`));
      ns.appendChild(row);
    });
    host.appendChild(ns);
  }
}
function chatSay(t){ const c=$("chat"); c.appendChild(el("div","say",t)); scroll(c); }
function chatYou(t){ const c=$("chat"); c.appendChild(el("div","you",t)); scroll(c); }
function chatEnd(t){ const c=$("chat"); c.appendChild(el("div","end",t)); scroll(c); }
function pushLog(m){ const c=$("log"); const row=el("div","row"); row.appendChild(el("span",(m.style||"muted"),m.text||"")); c.appendChild(row); scroll(c); }
function scroll(c){ if(S.autoscroll) c.scrollTop=c.scrollHeight; }
function showThinking(){
  if(S._thinking) return;
  const c=$("chat"); const b=el("div","say thinking");
  b.innerHTML='<span class="dots"><i></i><i></i><i></i></span>';
  c.appendChild(b); S._thinking=b; scroll(c);
}
function hideThinking(){ if(S._thinking){ S._thinking.remove(); S._thinking=null; } }
function submitCmd(){ const i=$("cmd"); const t=i.value.trim(); if(!t)return; chatYou(t); showThinking(); send({type:"action",text:t}); i.value=""; clearMenu(); }
$("sendBtn").onclick=submitCmd; $("cmd").addEventListener("keydown",e=>{ if(e.key==="Enter") submitCmd(); });
$("tradeBtn").onclick=()=>{ if(S.shop.open) send({type:"closeShop"}); else send({type:"openShop"}); };
function showMenu(m){ const bar=$("menuBar"); bar.innerHTML=""; bar.classList.remove("hidden"); if(m.text) pushLog({style:"system",text:m.text});
  (m.options||[]).forEach((opt,i)=>{ const b=el("button",null,`${i+1}. ${opt}`); b.onclick=()=>{ chatYou(opt); send({type:"action",text:String(i+1)}); clearMenu(); }; bar.appendChild(b); }); }
function clearMenu(){ const b=$("menuBar"); b.innerHTML=""; b.classList.add("hidden"); }
function makeSplitter(splitId,targetId,sign){ const split=$(splitId),target=$(targetId);
  split.addEventListener("mousedown",e=>{ e.preventDefault(); const sy=e.clientY, sh=target.offsetHeight;
    const move=ev=>{ const h=Math.max(48,sh+sign*(ev.clientY-sy)); target.style.flex="0 0 "+h+"px"; };
    const up=()=>{ document.removeEventListener("mousemove",move); document.removeEventListener("mouseup",up); document.body.style.userSelect=""; };
    document.body.style.userSelect="none"; document.addEventListener("mousemove",move); document.addEventListener("mouseup",up); }); }
makeSplitter("splitImage","imageArea",1); makeSplitter("splitChat","logWrap",-1);

// ===== CHARACTER sheet ======================================================
function renderPortraits(){ const box=$("portraits"); box.innerHTML="";
  S.party.forEach((p,i)=>{ const w=el("div","portrait"+(i===S.selectedPc?" sel":"")); w.style.setProperty("--pc-accent",(p.decoration&&p.decoration.accent)||"#c9a86a");
    w.appendChild(el("div","disc",(p.decoration&&p.decoration.class_glyph)||(p.name[0]||"?")));
    w.appendChild(el("div","pn",p.name)); w.appendChild(el("div","hp",`${p.hp}/${p.max_hp} hp`));
    w.onclick=()=>{ S.selectedPc=i; renderPortraits(); renderSheet(); }; box.appendChild(w); }); }

function renderSheet(){
  const host=$("sheet"); const p=S.party[S.selectedPc];
  if(!p){ host.innerHTML="<p class='muted'>No character.</p>"; return; }
  const d=p.decoration||{}; host.style.setProperty("--pc-accent",d.accent||"#c9a86a");
  const abilities=p.abilities.map(a=>`<div class="ab"><div class="ab-n">${a.label.slice(0,3)}</div><div class="ab-m">${a.mod}</div><div class="ab-s">${a.score}</div></div>`).join("");
  const saves=p.saves.map(s=>`<span class="save ${s.proficient?'prof':''}">${s.label} ${s.mod}</span>`).join("");
  const skills=p.skills.map(s=>`<div class="skill ${s.proficient?'prof':''}"><span class="dot"></span><span class="sa">${s.ability}</span><span>${s.label}</span><span class="sm">${s.mod}</span></div>`).join("");
  const chips=(arr)=>(arr&&arr.length)?arr.map(x=>`<span class="tag-chip">${x}</span>`).join(""):"<span class='muted'>—</span>";
  const atks=(p.attacks||[]).map(a=>`<span class="tag-chip">${a.name} ${a.bonus>=0?"+":""}${a.bonus} · ${a.damage}</span>`).join("")||"<span class='muted'>—</span>";
  const invRows=(p.inventory||[]).map(it=>`<tr class="inv-row" data-key="${it.key}"><td><span class="gem" style="background:${it.color}"></span>${it.name}</td><td class="muted">${cap(it.rarity||"")}</td></tr>`).join("");
  const invTable=(p.inventory&&p.inventory.length)?`<table class="inv-table"><tbody>${invRows}</tbody></table>`:"<span class='muted'>Empty</span>";
  const n=p.narrative||{};
  const narr=["trait","ideal","bond","flaw"].map(k=>n[k]?`<p><span class="lbl">${cap(k)}:</span> ${n[k]}</p>`:"").join("")+(n.feature?`<p><span class="lbl">Feature:</span> ${n.feature}</p>`:"");
  let genderLine="";
  if(p.gender){ const g=p.gender; let txt=cap(g.current||"—"); if(g.initial&&g.initial!==g.current) txt=`${cap(g.initial)} → ${cap(g.current)}`;
    if(g.dissonant) txt+=` · <span class="dissonant">settling (${g.dissonance_rests} rest${g.dissonance_rests===1?"":"s"})</span>`;
    genderLine=`<div class="sub">Gender: ${txt}</div>`; }
  const glyph=d.class_glyph||"✦";
  host.innerHTML=`
    <div class="sheet-top">
      <div class="portrait-box" title="Character portrait"><div class="portrait-ph" style="color:${d.accent||'#c9a86a'};border-color:${d.accent||'#c9a86a'}">${glyph}</div><div class="portrait-cap">portrait</div></div>
      <div class="banner">
        <div class="glyphs">${d.class_glyph||""} ${d.align_sigil||""}</div>
        <h2>${p.name}</h2>
        <div class="sub">${p.race} ${p.klass} · Level ${p.level}${p.background?` · ${p.background}`:""}</div>
        <div class="sub">${p.alignment||""} — <span class="muted">${p.condition||""}</span></div>
        ${genderLine}${d.motto?`<div class="motto">“${d.motto}”</div>`:""}
      </div>
    </div>
    <div class="grid">
      <div class="abilities">${abilities}</div>
      <div>
        <div class="stat-strip">
          <div class="pill shield"><div class="pn">AC</div><div class="pv">${p.ac}</div></div>
          <div class="pill"><div class="pn">HP</div><div class="pv">${p.hp}/${p.max_hp}</div></div>
          <div class="pill"><div class="pn">Init</div><div class="pv">${p.initiative}</div></div>
          <div class="pill"><div class="pn">Speed</div><div class="pv">${p.speed}</div></div>
          <div class="pill"><div class="pn">Prof</div><div class="pv">${p.proficiency_bonus}</div></div>
        </div>
        <div class="box"><h3>Saving Throws</h3><div class="saverow">${saves}</div></div>
        <div class="cols">
          <div><div class="box"><h3>Skills</h3>${skills}</div></div>
          <div>
            <div class="box"><h3>Attacks</h3><div class="tags">${atks}</div></div>
            <div class="box"><h3>Features &amp; Traits</h3><div class="tags">${chips((p.class_features||[]).concat(p.race_traits||[]))}</div></div>
            <div class="box"><h3>Languages</h3><div class="tags">${chips(p.languages)}</div></div>
            ${(p.resistances&&p.resistances.length)?`<div class="box"><h3>Resistances</h3><div class="tags">${chips(p.resistances)}</div></div>`:""}
            <div class="box"><h3>Inventory <span class="hint">tap an item</span></h3>${invTable}</div>
            <div class="box narr"><h3>Bonds &amp; Bearing</h3>${narr||"<span class='muted'>—</span>"}</div>
          </div>
        </div>
      </div>
    </div>
    ${renderSections(p.sections)}`;
  host.querySelectorAll(".inv-row").forEach(r=>r.onclick=()=>send({type:"itemDetail",key:r.dataset.key}));
}

// Extra sheet sections from add-ons: the first add-on that renders a section's kind wins.
function renderSections(sections){
  return (sections||[]).map(sec=>{ for(const x of ADDONS){ const h=x.sheetSection&&x.sheetSection(sec); if(h) return h; } return ""; }).join("");
}

// ===== SPELLBOOK ============================================================
function updateSpellbookTab(){
  const tab=$("tab-spellbook"); const has=(S.spellbook.casters||[]).length>0;
  tab.classList.toggle("hidden",!has);
  if(has && !S.spellbook.selected) S.spellbook.selected=S.spellbook.casters[0];
  if(!has && document.querySelector("#view-spellbook.active")) showTab("character");
  renderCasterList(); renderSpellbook();
}
function renderCasterList(){ const box=$("casterList"); box.innerHTML="";
  (S.spellbook.casters||[]).forEach(name=>{ const bk=S.spellbook.books[name]||{}; const w=el("div","portrait"+(name===S.spellbook.selected?" sel":""));
    w.appendChild(el("div","disc","✶")); w.appendChild(el("div","pn",name)); w.appendChild(el("div","hp",(bk.class||"caster")));
    w.onclick=()=>{ S.spellbook.selected=name; S.spellbook.draft=null; renderCasterList(); renderSpellbook(); }; box.appendChild(w); }); }

function draftFor(name){ const bk=S.spellbook.books[name]||{}; if(!S.spellbook.draft){
    S.spellbook.draft={ cantrips:(bk.cantrips||[]).slice(), spells:((bk.method==="known"?bk.known:bk.prepared)||[]).slice() }; }
  return S.spellbook.draft; }

function renderSpellbook(){
  const host=$("spellbook"); const name=S.spellbook.selected; const bk=name?S.spellbook.books[name]:null;
  if(!bk||!bk.caster){ host.innerHTML="<p class='muted'>No spellcaster selected.</p>"; return; }
  const draft=draftFor(name); const method=bk.method;
  const lvlKeys=Object.keys(bk.repertoire||{}).map(Number).sort((a,b)=>a-b);
  const cantripCells=(bk.all_cantrips||[]).map(sp=>spellCell(sp,draft.cantrips.includes(sp.key),"cantrip")).join("");
  let repHtml="";
  lvlKeys.forEach(lv=>{ const cells=bk.repertoire[lv].map(sp=>spellCell(sp,draft.spells.includes(sp.key),"spell")).join("");
    repHtml+=`<div class="spell-level"><h4>Level ${lv}</h4><div class="spell-grid">${cells}</div></div>`; });
  // prepared/known area, grouped by circle (level)
  const slots=bk.slots||{};
  const slotStr=Object.entries(slots).map(([k,v])=>`${k.replace("level_","L")}×${v}`).join("  ");
  const chosen=draft.spells.map(k=>spellByKey(bk,k)).filter(Boolean);
  const byLvl={}; chosen.forEach(sp=>{ (byLvl[sp.level]=byLvl[sp.level]||[]).push(sp); });
  let circles=""; Object.keys(byLvl).map(Number).sort((a,b)=>a-b).forEach(lv=>{
    const chips=byLvl[lv].map(sp=>`<span class="prep-chip" data-key="${sp.key}" title="remove">${sp.icon} ${sp.name}</span>`).join("");
    circles+=`<div class="circle"><div class="circle-n">${lv}</div><div class="circle-chips">${chips}</div></div>`; });
  const capLine=method==="known"?`Known ${draft.spells.length}/${bk.spells_count}`:`Prepared ${draft.spells.length}/${bk.spells_count}`;
  host.innerHTML=`
    <div class="sb-head">
      <h2>${name}'s Spellbook</h2>
      <div class="sb-meta">${bk.class} · ${bk.ability} · save DC ${bk.save_dc||"—"} · atk ${bk.attack_bonus>=0?"+":""}${bk.attack_bonus} · slots ${slotStr||"—"}</div>
    </div>
    <div class="box"><h3>Cantrips <span class="hint">${draft.cantrips.length}/${bk.cantrips_known}</span></h3><div class="spell-grid">${cantripCells}</div></div>
    <div class="box"><h3>Spellbook <span class="hint">tap to ${method==="known"?"learn":"prepare"} · tap again to remove</span></h3>${repHtml}</div>
    <div class="prepared-area" id="preparedArea">
      <div class="prep-head"><span>${capLine}</span><button id="savePrep" class="primary">Save preparation</button></div>
      <div class="circles">${circles||"<span class='muted'>Tap spells above to add them.</span>"}</div>
      <p class="muted prep-note">Preparation takes effect after a long rest.</p>
    </div>`;
  host.querySelectorAll(".spell-cell").forEach(c=>{ c.onclick=()=>toggleSpell(name,c.dataset.key,c.dataset.kind);
    c.setAttribute("draggable","true"); c.addEventListener("dragstart",e=>e.dataTransfer.setData("text/plain",JSON.stringify({key:c.dataset.key,kind:c.dataset.kind}))); });
  host.querySelectorAll(".prep-chip").forEach(c=>c.onclick=()=>toggleSpell(name,c.dataset.key,"spell"));
  const area=$("preparedArea");
  area.addEventListener("dragover",e=>{ e.preventDefault(); area.classList.add("drop"); });
  area.addEventListener("dragleave",()=>area.classList.remove("drop"));
  area.addEventListener("drop",e=>{ e.preventDefault(); area.classList.remove("drop");
    try{ const d=JSON.parse(e.dataTransfer.getData("text/plain")); if(d.kind==="spell") toggleSpell(name,d.key,"spell",true); }catch(_){} });
  $("savePrep").onclick=()=>savePreparation(name);
}
function spellCell(sp,on,kind){ return `<div class="spell-cell ${on?'on':''}" data-key="${sp.key}" data-kind="${kind}" title="${(sp.desc||'').replace(/"/g,'&quot;')}"><span class="sc-ic">${sp.icon}</span><span class="sc-nm">${sp.name}</span><span class="sc-lv">${kind==='cantrip'?'C':sp.level}</span></div>`; }
function spellByKey(bk,key){ for(const lv of Object.keys(bk.repertoire||{})){ const f=bk.repertoire[lv].find(s=>s.key===key); if(f) return f; } const c=(bk.all_cantrips||[]).find(s=>s.key===key); return c||null; }
function toggleSpell(name,key,kind,addOnly){
  const bk=S.spellbook.books[name]; const draft=draftFor(name);
  if(kind==="cantrip"){ const i=draft.cantrips.indexOf(key);
    if(i>=0 && !addOnly) draft.cantrips.splice(i,1); else if(i<0 && draft.cantrips.length<bk.cantrips_known) draft.cantrips.push(key); }
  else { const i=draft.spells.indexOf(key);
    if(i>=0 && !addOnly) draft.spells.splice(i,1); else if(i<0 && draft.spells.length<bk.spells_count) draft.spells.push(key); }
  renderSpellbook();
}
function savePreparation(name){ const bk=S.spellbook.books[name]; const draft=draftFor(name);
  send({type:"setCantrips", member:name, keys:draft.cantrips});
  send({type:(bk.method==="known"?"setKnown":"prepareSpells"), member:name, keys:draft.spells});
}

// ===== TRADE / SHOP ========================================================
function tradeList(side){ return side==="trader"?(S.shop.view.trader_items||[]):(S.shop.view.player_items||[]); }
function priceOf(side,key){ const it=tradeList(side).find(x=>x.key===key); return it?it.price:0; }
function renderTradePanel(){
  const v=S.shop.view; if(!v) return;
  $("tradePanel").classList.remove("hidden");
  $("traderName").textContent=(v.tradesman||{}).name||"a merchant";
  $("traderGold").textContent=(v.gold||0)+" gp";
  const db=$("traderDiscount"); if(v.discount>0){ db.classList.remove("hidden"); db.textContent="−"+v.discount+"% haggled"; } else db.classList.add("hidden");
  renderTradeList("player"); renderTradeList("trader"); renderDealTray();
  $("searchPlayer").oninput=()=>renderTradeList("player");
  $("searchTrader").oninput=()=>renderTradeList("trader");
  $("closeTrade").onclick=()=>send({type:"closeShop"});
  $("clearDeal").onclick=()=>{ S.shop.take=[]; S.shop.give=[]; renderDealTray(); };
  $("confirmDeal").onclick=()=>{ if(S.shop.take.length||S.shop.give.length) send({type:"tradeDeal",take:S.shop.take,give:S.shop.give}); };
  wireDrop($("takeItems"),"trader"); wireDrop($("giveItems"),"player");
}
function renderTradeList(side){
  const host=$(side==="trader"?"traderList":"playerList");
  const q=(($(side==="trader"?"searchTrader":"searchPlayer")||{}).value||"").toLowerCase();
  const hl=side==="trader"?S.shop.hl.give:S.shop.hl.take;   // given items land in trader list; taken in player list
  host.innerHTML="";
  const rows=tradeList(side).filter(it=>it.name.toLowerCase().includes(q));
  if(!rows.length){ host.appendChild(el("div","muted","— nothing —")); return; }
  rows.forEach(it=>{
    const r=el("div","trade-item"+(hl&&hl.includes(it.key)?" just-traded":""));
    r.draggable=true; r.dataset.key=it.key;
    r.innerHTML=`<span class="gem" style="background:${it.color}"></span><span class="ti-nm">${it.name}</span><span class="ti-pr">${it.price} gp</span>`;
    r.addEventListener("dragstart",e=>e.dataTransfer.setData("text/plain",JSON.stringify({key:it.key,side})));
    r.onclick=()=>addToDeal(side,it.key);
    host.appendChild(r);
  });
}
function addToDeal(side,key){
  const arr=side==="trader"?S.shop.take:S.shop.give;
  if(arr.filter(k=>k===key).length >= availCount(side,key)) return;   // can't exceed what's available
  arr.push(key); renderDealTray();
}
function removeOneKey(which,key){
  const a=which==="take"?S.shop.take:S.shop.give; const i=a.lastIndexOf(key);
  if(i>=0) a.splice(i,1); renderDealTray();
}
function availCount(side,key){ return tradeList(side).filter(x=>x.key===key).length; }
function groupCounts(arr){ const m=new Map(); arr.forEach(k=>m.set(k,(m.get(k)||0)+1)); return m; }
function renderTrayChips(host, arr, which, side){
  host.innerHTML="";
  groupCounts(arr).forEach((n,k)=>{
    const it=tradeList(side).find(x=>x.key===k)||{name:k};
    const atCap = n >= availCount(side,k);
    const c=el("span","deal-chip");
    c.innerHTML=`<button class="qbtn">−</button>`
      +`<span class="qn">${it.name}${n>1?` <b>×${n}</b>`:""}</span>`
      +`<button class="qbtn"${atCap?" disabled":""}>+</button>`;
    const [dec,inc]=c.querySelectorAll(".qbtn");
    dec.onclick=()=>removeOneKey(which,k);
    inc.onclick=()=>addToDeal(side,k);
    host.appendChild(c);
  });
}
function wireDrop(zone,acceptSide){
  zone.ondragover=e=>{e.preventDefault();zone.classList.add("drop");};
  zone.ondragleave=()=>zone.classList.remove("drop");
  zone.ondrop=e=>{e.preventDefault();zone.classList.remove("drop");
    try{ const d=JSON.parse(e.dataTransfer.getData("text/plain")); if(d.side===acceptSide) addToDeal(d.side,d.key); }catch(_){ } };
}
function renderDealTray(){
  renderTrayChips($("giveItems"), S.shop.give, "give", "player");
  renderTrayChips($("takeItems"), S.shop.take, "take", "trader");
  const cost=S.shop.take.reduce((s,k)=>s+priceOf("trader",k),0);
  const rev=S.shop.give.reduce((s,k)=>s+priceOf("player",k),0);
  const net=cost-rev, nd=$("dealNet");
  if(!S.shop.take.length && !S.shop.give.length){ nd.textContent="Drag items to build a deal"; nd.className="deal-net"; }
  else if(net>0){ nd.textContent=`You pay ${net} gp`; nd.className="deal-net pay"; }
  else if(net<0){ nd.textContent=`You receive ${-net} gp`; nd.className="deal-net recv"; }
  else { nd.textContent="Even trade"; nd.className="deal-net even"; }
  $("confirmDeal").disabled = !(S.shop.take.length||S.shop.give.length) || (net>(S.shop.view.gold||0));
}
function onDealResult(m){
  if(!m.ok){ pushLog({style:"crit-fail",text:m.message||"Deal failed."}); renderDealTray(); return; }
  S.shop.hl={take:(m.take||[]).slice(), give:(m.give||[]).slice()};
  S.shop.take=[]; S.shop.give=[];
  pushLog({style:"loot",text:"Trade — "+(m.message||"done")});
  setTimeout(()=>{ S.shop.hl={take:[],give:[]}; if(S.shop.open){ renderTradeList("player"); renderTradeList("trader"); } }, 2400);
}
function closeTradePanel(){ const p=$("tradePanel"); if(p) p.classList.add("hidden"); }

// ===== EQUIPMENT (paper-doll) ==============================================
const SLOT_ICON = {main_hand:"⚔",off_hand:"🛡",armor:"🥋",helm:"⛑",cloak:"🧥",gloves:"🧤",boots:"🥾",amulet:"📿",ring_1:"💍",ring_2:"💍"};
function renderEquipPortraits(){
  const box=$("equipPortraits"); box.innerHTML="";
  S.party.forEach((p,i)=>{ const w=el("div","portrait"+(p.name===S.equipment.member?" sel":""));
    w.style.setProperty("--pc-accent",(p.decoration&&p.decoration.accent)||"#c9a86a");
    w.appendChild(el("div","disc",(p.decoration&&p.decoration.class_glyph)||(p.name[0]||"?")));
    w.appendChild(el("div","pn",p.name)); w.appendChild(el("div","hp","AC "+p.ac));
    w.onclick=()=>{ S.selectedPc=i; S.equipment.msg=""; send({type:"equipment",member:p.name}); }; box.appendChild(w); });
}
function slotCell(s){
  const filled=!!s.item;
  const d=el("div","equip-slot"+(filled?" filled":"")+" grp-"+(s.group||"")); d.dataset.slot=s.slot;
  d.appendChild(el("div","slot-ic",SLOT_ICON[s.slot]||"▢"));
  d.appendChild(el("div","slot-lb",s.label));
  d.appendChild(el("div","slot-it",filled?s.item.name:"empty"));
  if(filled){ d.title="Tap to unequip "+s.item.name; d.onclick=()=>send({type:"unequip",member:S.equipment.member,slot:s.slot}); }
  d.addEventListener("dragover",e=>{e.preventDefault();d.classList.add("drop");});
  d.addEventListener("dragleave",()=>d.classList.remove("drop"));
  d.addEventListener("drop",e=>{e.preventDefault();d.classList.remove("drop");
    const key=e.dataTransfer.getData("text/plain"); if(key) send({type:"equip",member:S.equipment.member,key,slot:s.slot}); });
  return d;
}
function renderEquipScreen(){
  const host=$("equipScreen"); const v=S.equipment.view;
  if(!v||!v.slots){ host.innerHTML="<p class='muted'>No equipment data.</p>"; return; }
  const slotBy=k=>v.slots.find(s=>s.slot===k)||{slot:k,label:k,group:"",item:null};
  const enc=v.encumbrance||{}; const pct=enc.capacity?Math.min(100,Math.round(100*(enc.weight||0)/enc.capacity)):0;
  const member=S.party.find(p=>p.name===S.equipment.member)||{};
  const hd=member.hit_dice||{remaining:0,total:0,die:8};
  const invRows=(S.equipment.inventory||[]).map(it=>`<div class="equip-inv-item${it.equippable?' equippable':''}" draggable="${it.equippable}" data-key="${it.key}" data-slot="${it.slot}"><span class="gem" style="background:${it.color}"></span><span class="ei-nm">${it.name}</span>${it.equippable?'<span class="eq-hint">equip</span>':''}</div>`).join("")||"<span class='muted'>Nothing carried.</span>";
  const bonuses=Object.entries(v.bonuses||{}).filter(([k])=>k!=="ac"&&k!=="weapon").map(([k,n])=>`<span class="tag-chip">${cap(k)} +${n}</span>`).join("");
  host.innerHTML=`
    <div class="equip-head"><h2>${S.equipment.member}</h2>
      <div class="equip-stats"><span class="ac-badge">AC ${v.ac}</span>
        <span class="enc-status enc-${(enc.status||'').replace(/ /g,'-')}">${enc.status||''}</span></div></div>
    ${S.equipment.msg?`<div class="equip-msg">${S.equipment.msg}</div>`:""}
    <div class="paperdoll">
      <div class="slot-col" id="slotsLeft"></div>
      <div class="figure"><div class="figure-body">${(member.decoration||{}).class_glyph||"🧍"}</div>
        <div class="figure-cap">${member.klass||""}</div>${bonuses?`<div class="figure-bonus">${bonuses}</div>`:""}</div>
      <div class="slot-col" id="slotsRight"></div>
    </div>
    <div class="enc-bar-wrap"><div class="enc-bar"><div class="enc-fill ${enc.over?'over':''}" style="width:${pct}%"></div></div>
      <div class="enc-cap">${enc.weight||0} / ${enc.capacity||0} lb${enc.speed_penalty?` · speed ${enc.speed_penalty}`:""}</div></div>
    <div class="rest-row"><span>Hit dice: <b>${hd.remaining}/${hd.total}</b> (d${hd.die||8})</span>
      <button id="shortRestBtn" class="ghost"${hd.remaining>0?"":" disabled"}>Short rest — spend 1 die</button></div>
    <div class="box"><h3>Carried <span class="hint">drag onto a slot, or tap to equip</span></h3>
      <div class="equip-inv" id="equipInv">${invRows}</div></div>`;
  ["main_hand","off_hand","armor","helm","cloak"].forEach(k=>$("slotsLeft").appendChild(slotCell(slotBy(k))));
  ["gloves","boots","amulet","ring_1","ring_2"].forEach(k=>$("slotsRight").appendChild(slotCell(slotBy(k))));
  host.querySelectorAll(".equip-inv-item").forEach(row=>{
    if(row.classList.contains("equippable")){
      row.onclick=()=>equipToNatural(row.dataset.key,row.dataset.slot);
      row.addEventListener("dragstart",e=>e.dataTransfer.setData("text/plain",row.dataset.key));
    } else row.onclick=()=>send({type:"itemDetail",key:row.dataset.key});
  });
  const sr=$("shortRestBtn"); if(sr) sr.onclick=()=>send({type:"shortRest",member:S.equipment.member,dice:1});
}
function equipToNatural(key,slot){
  if(slot==="ring_1"||slot==="ring_2"){ const v=S.equipment.view;
    const free=["ring_1","ring_2"].find(s=>{ const sl=v.slots.find(x=>x.slot===s); return sl&&!sl.item; });
    slot=free||"ring_1"; }
  S.equipment.msg=""; send({type:"equip",member:S.equipment.member,key,slot});
}

// ===== DETAIL MODAL =========================================================
function showDetail(html){ $("detailBody").innerHTML=html; $("detail").classList.remove("hidden"); }
function closeDetail(){ $("detail").classList.add("hidden"); }
$("detailClose").onclick=closeDetail;
$("detail").addEventListener("click",e=>{ if(e.target.id==="detail") closeDetail(); });
function itemDetailHtml(it){
  if(!it||!it.found) return `<h2>${(it&&it.name)||"Unknown item"}</h2><p class="muted">No details available.</p>`;
  const bonuses=(it.bonuses&&it.bonuses.length)?`<p><span class="lbl">Bonuses:</span> ${it.bonuses.join(", ")}</p>`:"";
  const att=it.attunement?`<span class="tag-chip">requires attunement</span>`:"";
  return `<div class="detail-card" style="border-color:${it.rarity_color}">
    <h2 style="color:${it.rarity_color}">${it.name}</h2>
    <div class="sub">${cap(it.category)} · ${cap(it.rarity)} · ${it.value} gp ${att}</div>
    ${bonuses}${it.effects?`<p><span class="lbl">Effect:</span> ${it.effects}</p>`:""}
    ${it.lore?`<p class="lore">${it.lore}</p>`:""}${it.special?`<p class="special">${it.special}</p>`:""}
  </div>`;
}

// ===== SAVES / INFO / SETTINGS =============================================
$("saveBtn").onclick=()=>send({type:"save",slot:$("saveSlot").value.trim()||"save"});
function flashSave(t,bad){ const m=$("saveMsg"); if(m){ m.textContent=t; m.style.color=bad?"var(--bad)":"var(--good)"; } }
function renderSaves(saves){ const box=$("savesList"); if(!box)return; box.innerHTML="";
  if(!saves.length){ box.appendChild(el("div","muted","No saves yet.")); return; }
  saves.forEach(s=>{ const e=el("div","save-entry"); const main=el("div","se-main");
    main.appendChild(el("div",null,`${s.pc_name||"?"} — ${s.slot}`)); main.appendChild(el("div","se-sub",`${s.location||""}${s.saved_at?" · "+s.saved_at:""}`));
    e.appendChild(main); const b=el("button","primary","Load"); b.onclick=()=>send({type:"load",slot:s.slot}); e.appendChild(b); box.appendChild(e); }); }
function renderInfo(m){ const v=m.versions||{}; const kv=$("versionsBox"); if(!kv)return; kv.innerHTML="";
  const add=(k,val)=>{ kv.appendChild(el("b",null,k)); kv.appendChild(el("div",null,val)); };
  if(v.ruleset) add("Ruleset",`${v.ruleset.name} v${v.ruleset.version} (${v.ruleset.status||""})`);
  if(v.setting) add("World",`${v.setting.name}${v.setting.tone?" — "+v.setting.tone:""}`);
  if(v.story) add("Story",v.story.name); if(v.engine) add("Engine","v"+v.engine);
  const rl=$("rulesList"); rl.innerHTML=""; (m.rules||[]).forEach(r=>rl.appendChild(el("li",null,r.name)));
  const ol=$("optList"); ol.innerHTML="";
  (m.optional||[]).forEach(o=>{ const row=el("label","opt"); const left=el("span"); left.appendChild(el("span",null,o.name));
    left.appendChild(el("span","badge",o.implemented?"ready":"planned")); if(o.note) left.appendChild(el("small",null,o.note));
    const cb=el("input"); cb.type="checkbox"; cb.checked=!!o.on; cb.disabled=!o.implemented; cb.onchange=()=>send({type:"setRule",key:o.key,on:cb.checked});
    row.appendChild(left); row.appendChild(cb); ol.appendChild(row); });
  const sb=$("statsBox"); sb.innerHTML=""; const st=m.stats||{};
  const stat=(k,val)=>{ sb.appendChild(el("b",null,k)); sb.appendChild(el("div",null,String(val))); };
  if(st.items_total!=null) stat("Items",`${st.items_total} (${st.items_tradeable||0} tradeable)`);
  (st.extra||[]).forEach(e=>stat(e.label,e.value));
  if(st.npcs!=null) stat("NPCs",st.npcs); if(st.locations!=null) stat("Locations",st.locations);
  if(st.tradesmen!=null) stat("Tradesmen",st.tradesmen); if(st.scenes!=null) stat("Authored scenes",st.scenes);
  if(st.items_by_rarity){ const wrap=el("div"); wrap.style.gridColumn="1 / -1"; const sw=el("div","swatches");
    Object.entries(st.items_by_rarity).forEach(([r,n])=>{ const s=el("span","swatch",`${r.replace("_"," ")}: ${n}`); s.style.background=RARITY[r]||"#b9c2cc"; sw.appendChild(s); });
    sb.appendChild(el("b",null,"By rarity")); wrap.appendChild(sw); sb.appendChild(wrap); } }
$("optTheme").onchange=e=>document.body.dataset.theme=e.target.value;
$("optText").onchange=e=>document.documentElement.dataset.textsize=e.target.value;
$("optAutoscroll").onchange=e=>S.autoscroll=e.target.checked;

connect();

// ===== LEVEL UP ============================================================
function luState(){ return S.levelup || (S.levelup={party:[],roadmaps:{},selected:0,available:0,modalOpen:false,wantModal:false}); }
function onLevelUp(m){
  const L=luState(); L.party=m.party||[]; L.roadmaps=m.roadmaps||{}; L.available=m.available||0;
  if(L.selected>=L.party.length) L.selected=0;
  const cur=L.party[L.selected];
  // a fresh milestone just granted from the FAB -> pop the advancement chooser open (clear the
  // request either way, so a no-op grant at level 20 doesn't leave it armed)
  if(L.wantModal){ if(cur && cur.available) L.modalOpen=true; L.wantModal=false; }
  // the pending level-up was applied or cancelled -> the chooser has nothing left to show
  if(L.modalOpen && (!cur || !cur.available)) L.modalOpen=false;
  updateLuBadge();
  if(document.querySelector("#view-levelup.active")) renderLevelup();
}
function updateLuBadge(){
  const L=luState(), b=$("luBadge"), tab=document.querySelector('.tab[data-tab="levelup"]');
  if(L.available>0){ b.classList.remove("hidden"); b.textContent=L.available; if(tab) tab.classList.add("alert"); }
  else { b.classList.add("hidden"); if(tab) tab.classList.remove("alert"); }
}
function luSelect(i){ const L=luState(); if(i!==L.selected) L.modalOpen=false; L.selected=i; renderLevelup(); }
function renderLevelup(){ renderLuParty(); renderLuGraph(); renderLuFab(); renderLuModal(); }

function renderLuParty(){
  const L=luState(), host=$("luParty"); host.innerHTML="";
  host.appendChild(el("div","lu-h","Party"));
  if(!L.party.length){ host.appendChild(el("div","lu-note","No party loaded.")); return; }
  L.party.forEach((c,i)=>{
    const it=el("button","lu-mem"+(i===L.selected?" sel":"")+(c.available?" alert":""));
    const orb=el("span","lu-orb"); orb.style.background=c.color; orb.textContent=c.glyph; it.appendChild(orb);
    const meta=el("div","lu-meta");
    meta.appendChild(el("div","lu-nm",c.name));
    meta.appendChild(el("div","lu-sub",`${c.class_label} ${c.level}`+(c.subclass_label?" · "+c.subclass_label:"")));
    it.appendChild(meta);
    if(c.available) it.appendChild(el("span","lu-dot"));
    it.onclick=()=>luSelect(i); host.appendChild(it);
  });
  host.appendChild(el("div","lu-foot","A glowing dot marks a pending level-up."));
}

// icon shown inside a level circle: subclass-choice level, an ASI, a feature, or nothing.
function luNodeIcon(rm,lvl){
  const feats=(rm.rows&&rm.rows[lvl-1]&&rm.rows[lvl-1].features)||[];
  if(lvl===rm.subclass_level) return "❖";
  if(feats.some(f=>/Ability Score Improvement/i.test(f))) return "✦";
  if(feats.length) return rm.glyph||"◆";
  return "";
}
function luNodeTitle(rm,lvl,subKey){
  let feats=((rm.rows&&rm.rows[lvl-1]&&rm.rows[lvl-1].features)||[]).slice();
  const sc=subKey&&rm.subclasses&&rm.subclasses[subKey];
  if(sc&&sc.features&&sc.features[String(lvl)]) feats=feats.concat(sc.features[String(lvl)]);
  return `Level ${lvl}`+(feats.length?": "+feats.join(", "):"");
}
// ---- the character's progression tree (right-hand free field) --------------
function luLanes(c){
  const L=luState();
  const lanes=(c.classes&&c.classes.length)?c.classes.slice():[{class_key:c.class_key,
    label:c.class_label,level:c.level,subclass:c.subclass,subclass_label:c.subclass_label,
    color:c.color,glyph:c.glyph}];
  // a provisional lane for a pending "add a class", so the branch into it is visible on the tree
  if(c.available && c.is_new_class && c.chosen_class && !lanes.some(l=>l.class_key===c.chosen_class)){
    const rm=L.roadmaps[c.chosen_class]||{};
    lanes.push({class_key:c.chosen_class,label:rm.label||c.chosen_class,level:0,subclass:"",
      subclass_label:"",color:rm.color||"#b07a2c",provisional:true});
  }
  return lanes;
}
function renderLuGraph(){
  const L=luState(), host=$("luGraph"); host.innerHTML="";
  const c=L.party[L.selected];
  if(!c){ host.appendChild(el("div","lu-note","Select a party member to see their path.")); return; }
  const lanes=luLanes(c);
  const anyRoad=lanes.some(l=>L.roadmaps[l.class_key]&&(L.roadmaps[l.class_key].rows||[]).length);
  const tree=el("div","lu2-tree");
  // root: the hero, from which each class branch grows
  const root=el("div","lu2-root"); root.style.setProperty("--lane",c.color||"#b07a2c");
  const orb=el("div","lu2-root-orb"); orb.textContent=c.glyph||"✦"; root.appendChild(orb);
  root.appendChild(el("div","lu2-root-nm",c.name));
  root.appendChild(el("div","lu2-root-sub","Level "+c.level));
  tree.appendChild(root);
  if(!anyRoad){ tree.appendChild(el("div","lu-note","No progression track for this character.")); host.appendChild(tree); return; }
  const branches=el("div","lu2-branches");
  lanes.forEach(l=>{
    const rm=L.roadmaps[l.class_key]; if(!rm||!(rm.rows||[]).length) return;
    const lane=el("div","tree-lane"+(l.provisional?" prov":"")); lane.style.setProperty("--lane",l.color||"#b07a2c");
    const lh=el("div","tree-lane-h");
    lh.appendChild(el("span","tree-lane-glyph",rm.glyph||l.glyph||"◆"));
    lh.appendChild(el("span","tree-lane-nm",`${l.label} ${l.level}`+(l.subclass_label?" · "+l.subclass_label:"")));
    lane.appendChild(lh);
    const spine=el("div","tree-spine");
    (rm.rows||[]).forEach(row=>{
      const lvl=row.level;
      const advancing=c.available && c.chosen_class===l.class_key && lvl===c.class_target_level;
      let st="tnode"; st+= lvl<=l.level ? " got" : (advancing ? " next" : " future");
      const node=el("div",st); node.title=luNodeTitle(rm,lvl,l.subclass);
      const disc=el("div","tnode-disc"); disc.textContent=luNodeIcon(rm,lvl)||String(lvl); node.appendChild(disc);
      node.appendChild(el("div","tnode-lv",lvl));
      // a couple of feature leaves under milestone nodes (kept short so the tree stays readable)
      const feats=((rm.rows&&rm.rows[lvl-1]&&rm.rows[lvl-1].features)||[]);
      if(feats.length && (lvl<=l.level || advancing)){
        const leaf=el("div","tnode-leaf"); leaf.textContent=feats[0]; node.appendChild(leaf);
      }
      spine.appendChild(node);
    });
    lane.appendChild(spine);
    // the subclass branch — chosen one lit, alternatives shown faint (chosen in the modal)
    if(rm.subclasses && Object.keys(rm.subclasses).length){
      const fan=el("div","tree-fan"); fan.appendChild(el("span","tree-fan-h",`${cap(rm.subclass_noun||"subclass")} @ L${rm.subclass_level}`));
      Object.keys(rm.subclasses).forEach(sk=>{
        const sv=rm.subclasses[sk], chosen=l.subclass===sk;
        const chip=el("div","fan-node"+(chosen?" got":"")+(l.subclass&&!chosen?" dim":""));
        chip.textContent=sv.label; chip.title=sv.blurb||sv.label; fan.appendChild(chip);
      });
      lane.appendChild(fan);
    }
    branches.appendChild(lane);
  });
  tree.appendChild(branches);
  host.appendChild(tree);
}

// ---- floating advancement controls (bottom-left of the canvas) -------------
function renderLuFab(){
  const L=luState(), host=$("luFab"); host.innerHTML="";
  const c=L.party[L.selected]; if(!c) return;
  if(c.available){
    const adv=el("button","lu-fab-btn primary",`⇧ Advancement — reach Lv ${c.target_level}`);
    adv.onclick=()=>{ L.modalOpen=true; renderLuModal(); }; host.appendChild(adv);
    const rest=el("button","lu-fab-btn"+(c.ready?"":" wait"),"🌙 Long Rest — apply");
    rest.onclick=()=>send({type:"longRest"}); host.appendChild(rest);
  } else {
    const grant=el("button","lu-fab-btn primary",`✚ Advance ${c.name}`);
    grant.onclick=()=>{ L.wantModal=true; send({type:"levelAward",member:c.name}); };
    host.appendChild(grant);
    host.appendChild(el("div","lu-fab-note","Milestone advance — opens the class chooser."));
  }
}

// ---- the advancement chooser modal (opens like the creation wizard) --------
function glyphFor(kind){ return ({class:"✚",subclass:"❖",asi:"✦",expertise:"◎",spells:"✶"})[kind]||"•"; }
function luChoose(c,s,id){
  let val=id;
  if(s.choose>1){ const cur=(c.choices[s.key]||[]).slice(); const i=cur.indexOf(id);
    if(i>=0) cur.splice(i,1); else if(cur.length<s.choose) cur.push(id); val=cur; }
  send({type:"levelChoose",member:c.name,slot:s.key,value:val});
}
function closeLuModal(){ luState().modalOpen=false; renderLuModal(); }
function renderLuModal(){
  const L=luState(), modal=$("luModal");
  const c=L.party[L.selected];
  if(!L.modalOpen || !c){ modal.classList.add("hidden"); return; }
  modal.classList.remove("hidden");
  $("luModalTitle").textContent=`Advance ${c.name}`+(c.available?` → Level ${c.target_level}`:"");
  const body=$("luModalBody"); body.innerHTML="";
  if(!c.available){ body.appendChild(el("div","lu-note","No level-up is pending.")); }
  else {
    body.appendChild(el("div","lu-note ok","Choose this level's advances. They append to the character's path and apply on the next long rest — revise freely until then."));
    if(!c.slots.length) body.appendChild(el("div","lu-note","No choices this level — just rest to confirm."));
    c.slots.forEach(s=>{
      const sec=el("div","lu-slot");
      sec.appendChild(el("div","lu-slot-h", s.label+(s.choose>1?` (pick ${s.choose})`:"")));
      const chosen=c.choices[s.key];
      const isSel=(id)=> s.choose>1 ? (chosen||[]).includes(id) : chosen===id;
      const grid=el("div","lu-grid");
      s.options.forEach(o=>{
        const card=el("button","lu-opt"+(isSel(o.id)?" sel":""));
        card.appendChild(el("span","lu-opt-ic",glyphFor(s.kind)));
        const t=el("div","lu-opt-t"); t.appendChild(el("div","lu-opt-nm",o.label));
        if(o.desc) t.appendChild(el("div","lu-opt-d",o.desc));
        card.appendChild(t); card.onclick=()=>luChoose(c,s,o.id); grid.appendChild(card);
      });
      sec.appendChild(grid); body.appendChild(sec);
    });
  }
  const foot=$("luModalFoot"); foot.innerHTML="";
  if(c.available){
    const rest=el("button","lu-btn"+(c.ready?"":" wait"),"🌙 Long Rest — apply"); rest.onclick=()=>send({type:"longRest"});
    const cancel=el("button","lu-btn ghost","Cancel level"); cancel.onclick=()=>send({type:"levelCancel",member:c.name});
    const close=el("button","lu-btn ghost","Close"); close.onclick=closeLuModal;
    foot.appendChild(rest); foot.appendChild(cancel); foot.appendChild(close);
  }
}
$("luModalClose").onclick=closeLuModal;
$("luModal").addEventListener("click",e=>{ if(e.target===$("luModal")) closeLuModal(); });

// ===== LLM (llama-cpp) settings ============================================
// opts (optional): {locked:bool, pinned:number, note:string}. A locked row is disabled and greyed;
// a pinned value overrides `val` and locks the row so it visibly shows the value the backend forces.
function llmNumRow(label,id,val,min,max,step,opts){
  opts=opts||{};
  const pinned=(opts.pinned!=null&&opts.pinned!=="");
  if(pinned) val=opts.pinned;
  const locked=!!opts.locked||pinned;
  const row=el("label","opt"+(locked?" locked":"")); row.appendChild(el("span",null,label));
  const wrap=el("div","llm-num"+(locked?" locked":""));
  const rng=document.createElement("input"); rng.type="range"; rng.min=min; rng.max=max; rng.step=step; rng.value=val;
  const num=document.createElement("input"); num.type="number"; num.id=id; num.min=min; num.max=max; num.step=step; num.value=val; num.className="llm-numin";
  if(locked){ rng.disabled=true; num.disabled=true; }
  else { rng.oninput=()=>{ num.value=rng.value; }; num.oninput=()=>{ rng.value=num.value; }; }
  wrap.appendChild(rng); wrap.appendChild(num); row.appendChild(wrap);
  const note=opts.note||(pinned?"fixed by this backend":(locked?"not sent to this backend":""));
  if(locked&&note) row.appendChild(el("span","muted lock-note",note));
  return row;
}
// ===== MODEL CONNECTION (lobby + LLM tab) ===================================
// The game connects to whatever backend serves the model -- native llama.cpp, or any
// OpenAI-compatible API (KoboldCpp, oobabooga, LM Studio, vLLM, a hosted provider). The user
// loads the model however they like (partial GPU/RAM offload, etc.); this just consumes the API.
const CONN_KINDS=[["canned","Canned (no model)"],["llama-cpp","llama.cpp server (native)"],
                  ["openai","OpenAI-compatible API"]];
const CONN_ENDPOINTS=[["completions","Text completions  (/v1/completions)"],
                      ["chat","Chat  (/v1/chat/completions)"]];
function connSelect(id,opts,cur){ const s=el("select"); s.id=id;
  opts.forEach(([v,label])=>{ const o=el("option",null,label); o.value=v; if(v===cur)o.selected=true; s.appendChild(o); });
  return s; }
function connRow(label,node){ const w=el("label","opt"); w.appendChild(el("span",null,label)); w.appendChild(node); return w; }
function connInput(id,type,ph,val){ const i=el("input"); i.id=id; i.type=type; if(ph)i.placeholder=ph; i.value=val||""; i.className="llm-url"; return i; }
function readConn(p){ const g=id=>{ const e=$(id); return e?e.value:""; };
  return {kind:g(p+"Kind"), base_url:g(p+"Url"), endpoint:g(p+"Ep"), model:g(p+"Model"),
          api_key:g(p+"Key"), timeout:g(p+"Timeout")}; }
// Build the connection form into `host`. `p` is an id prefix so the lobby ("lc") and LLM tab
// ("llmc") copies don't collide. Edits auto-save (persist + live-swap a running game).
function connectionControls(host,conn,p){
  conn=conn||{kind:"canned"};
  const kind=connSelect(p+"Kind",CONN_KINDS,conn.kind||"canned");
  host.appendChild(connRow("Backend",kind));
  const oai=el("div","conn-oai");
  // Keep direct handles to every field: this form is often built detached (LLM tab) and only
  // appended to the document afterwards, so we can't re-find the controls via getElementById here.
  const urlIn=connInput(p+"Url","text","http://127.0.0.1:8080",conn.base_url);
  const epSel=connSelect(p+"Ep",CONN_ENDPOINTS,conn.endpoint||"completions");
  const modelIn=connInput(p+"Model","text","(often ignored by local servers)",conn.model);
  const keyIn=connInput(p+"Key","password","(only for hosted APIs)",conn.api_key);
  const toIn=connInput(p+"Timeout","text","120",conn.timeout==null?"":conn.timeout);
  const urlRow=connRow("Server URL",urlIn);
  const epRow=connRow("API style",epSel);
  const modelRow=connRow("Model name",modelIn);
  const keyRow=connRow("API key",keyIn);
  const toRow=connRow("Timeout (s)",toIn);
  toRow.appendChild(el("span","muted","Raise this for big models — a slow CPU generation can take minutes."));
  oai.appendChild(urlRow); oai.appendChild(epRow); oai.appendChild(modelRow); oai.appendChild(keyRow);
  oai.appendChild(toRow);
  host.appendChild(oai);
  const bar=el("div","llm-actions");
  const test=el("button","ghost","Test connection"); test.type="button";
  const status=el("span","muted"); status.id=p+"Status";
  bar.appendChild(test); bar.appendChild(status); host.appendChild(bar);
  const sync=()=>{ const k=kind.value, isOai=(k==="openai");
    oai.style.display=(k==="canned")?"none":""; test.style.display=(k==="canned")?"none":"";
    [epRow,modelRow,keyRow].forEach(r=>r.style.display=isOai?"":"none"); };
  sync();
  const save=()=>{ sync(); send({type:"saveConnection",connection:readConn(p)}); };
  kind.onchange=save; epSel.onchange=save;
  [urlIn,modelIn,keyIn,toIn].forEach(e=>{ e.onchange=save; });
  test.onclick=()=>{ const st=$(p+"Status"); if(st){ st.textContent="Testing…"; st.className="muted"; }
    send({type:"saveConnection",connection:readConn(p)}); send({type:"testConnection",connection:readConn(p)}); };
}
function renderConnBar(){ const body=$("lobbyConnBody"); if(!body)return; body.innerHTML="";
  connectionControls(body,S.connection,"lc");
  const bl=$("lobbyBackend"); if(bl) bl.textContent=S.backend||"…"; }
// Remember the backend's sampler lock/pin view so the LLM tab can grey the fields it won't send.
function _stashRestrictions(m){ if(m&&m.restrictions){ S.llm=S.llm||{settings:{},models:[],runtime:{}};
  S.llm.runtime=S.llm.runtime||{}; S.llm.runtime.restrictions=m.restrictions; } }
function _llmActive(){ return !!document.querySelector("#view-llm.active"); }
function onConnectionSaved(m){ S.connection=m.connection||S.connection; S.backend=m.backend||S.backend;
  _stashRestrictions(m);
  const bl=$("lobbyBackend"); if(bl) bl.textContent=S.backend;
  const rt=$("llmBackendLine"); if(rt) rt.textContent="Backend: "+S.backend+(m.applied_live?"  ·  applied to the running game.":"  ·  used when you start a game.");
  if(m.restrictions&&_llmActive()) renderLlm(); }
function onConnectionTest(m){ _stashRestrictions(m); const txt=(m.ok?"✓ ":"✗ ")+(m.message||"");
  // A probe can reveal new pins/drops -> refresh the greyed fields, then restore the status text.
  if(m.restrictions&&_llmActive()) renderLlm();
  ["lcStatus","llmcStatus"].forEach(id=>{ const st=$(id); if(st){ st.textContent=txt; st.className=m.ok?"ok":"bad"; } }); }

function renderLlm(m){
  if(m){ S.llm={settings:m.settings||{},models:m.models||[],runtime:m.runtime||{}};
    if(m.connection){ S.connection=m.connection; } if(m.runtime&&m.runtime.backend){ S.backend=m.runtime.backend; } }
  const host=$("llmScreen"); if(!host||!S.llm) return; host.innerHTML="";
  const s=S.llm.settings, rt=S.llm.runtime||{};

  const status=el("div","card"); status.appendChild(el("h2",null,"LLM backend"));
  const st=el("p","muted"); st.id="llmBackendLine"; st.textContent="Backend: "+(rt.backend||"—")
    +(rt.fake?"  ·  sampling is saved but only bites with a real model."
             :"  ·  sampling changes apply live to the running model.");
  status.appendChild(st); host.appendChild(status);

  const cc=el("div","card"); cc.appendChild(el("h2",null,"Connection"));
  cc.appendChild(el("p","muted","Point the game at any model backend. Changes apply to the running game and are used for the next one."));
  connectionControls(cc,S.connection,"llmc");
  host.appendChild(cc);

  // Per-field lock/pin state for the current backend (from the server). Greyed rows won't be sent;
  // pinned rows show the single value the backend forces.
  const restr=(rt.restrictions)||{locked:[],pinned:{}};
  const lockOf=field=>{ const o={}; if((restr.locked||[]).indexOf(field)>=0) o.locked=true;
    if(restr.pinned&&restr.pinned[field]!=null) o.pinned=restr.pinned[field]; return o; };
  const c1=el("div","card"); c1.appendChild(el("h2",null,"Sampling (applies live)"));
  c1.appendChild(llmNumRow("Temperature","llmTemp",s.temperature,0,2,0.05,lockOf("temperature")));
  c1.appendChild(llmNumRow("Top-p","llmTopP",s.top_p,0,1,0.05,lockOf("top_p")));
  c1.appendChild(llmNumRow("Top-k","llmTopK",s.top_k,0,200,1,lockOf("top_k")));
  c1.appendChild(llmNumRow("Min-p","llmMinP",s.min_p,0,1,0.01,lockOf("min_p")));
  c1.appendChild(llmNumRow("Repeat penalty","llmRepPen",s.repeat_penalty,0,2,0.05,lockOf("repeat_penalty")));
  c1.appendChild(llmNumRow("Frequency penalty","llmFreqPen",s.frequency_penalty,-2,2,0.05,lockOf("frequency_penalty")));
  c1.appendChild(llmNumRow("Presence penalty","llmPresPen",s.presence_penalty,-2,2,0.05,lockOf("presence_penalty")));
  c1.appendChild(llmNumRow("Max tokens","llmMaxTok",s.max_tokens,16,4096,16,lockOf("max_tokens")));
  c1.appendChild(llmNumRow("Seed (−1 = random)","llmSeed",s.seed,-1,2147483647,1,lockOf("seed")));
  c1.appendChild(el("p","muted","Greyed rows aren’t sent to the current backend (top-k, min-p and "
    +"repeat penalty are llama.cpp-only; strict hosted APIs like Kimi/Grok also drop the penalties "
    +"and seed and pin temperature/top-p to a fixed value)."));
  host.appendChild(c1);

  // Narrator system prompt — replaces the engine's built-in narrator instructions when set.
  const cp=el("div","card"); cp.appendChild(el("h2",null,"Narrator system prompt"));
  cp.appendChild(el("p","muted","Optional. When set, this REPLACES the built-in narrator instructions "
    +"(voice, register, and pacing). The per-character briefing is still added so the prose stays "
    +"grounded. Leave blank to use the default. Applies live."));
  const spRow=el("label","opt sp-row"); spRow.appendChild(el("span",null,"System prompt"));
  const sp=document.createElement("textarea"); sp.id="llmSysPrompt"; sp.className="llm-sysprompt";
  sp.rows=6; sp.value=s.system_prompt||""; sp.placeholder="(blank = engine default narrator prompt)";
  spRow.appendChild(sp); cp.appendChild(spRow);
  host.appendChild(cp);

  host.appendChild(configCard(s));

  const c2=el("div","card"); c2.appendChild(el("h2",null,"Launch parameters (next launch.bat)"));
  const dirRow=el("label","opt"); dirRow.appendChild(el("span",null,"Models folder"));
  const dir=document.createElement("input"); dir.id="llmModelsDir"; dir.type="text";
  dir.value=s.models_dir||""; dir.className="llm-url"; dir.placeholder="(default: llm/models/)";
  dirRow.appendChild(dir); c2.appendChild(dirRow);
  const rescan=el("button","ghost","Save folder & rescan for models");
  rescan.onclick=()=>send({type:"saveLlamaSettings", settings:{models_dir:($("llmModelsDir")||{}).value||""}});
  c2.appendChild(rescan);
  const modelRow=el("label","opt"); modelRow.appendChild(el("span",null,"Model (.gguf)"));
  const sel=document.createElement("select"); sel.id="llmModel";
  const models=(S.llm.models&&S.llm.models.length)?S.llm.models:(s.model?[s.model]:[]);
  if(!models.length){ const o=document.createElement("option"); o.value=""; o.textContent="(no models in llm/models/)"; sel.appendChild(o); }
  models.forEach(mm=>{ const o=document.createElement("option"); o.value=mm; o.textContent=mm; if(mm===s.model)o.selected=true; sel.appendChild(o); });
  modelRow.appendChild(sel); c2.appendChild(modelRow);
  c2.appendChild(llmNumRow("Context size","llmCtx",s.context_size,512,131072,512));
  c2.appendChild(llmNumRow("GPU layers","llmNgl",s.gpu_layers,0,999,1));
  const urlRow=el("label","opt"); urlRow.appendChild(el("span",null,"Server URL"));
  const url=document.createElement("input"); url.id="llmUrl"; url.type="text"; url.value=s.server_url||""; url.className="llm-url";
  urlRow.appendChild(url); c2.appendChild(urlRow);
  c2.appendChild(el("p","muted","Model, context size, and GPU layers take effect the next time you start the model with launch.bat."));
  host.appendChild(c2);

  const bar=el("div","llm-actions");
  const save=el("button","primary","Save settings"); save.onclick=saveLlm; bar.appendChild(save);
  const note=el("span","muted"); note.id="llmSaveNote"; bar.appendChild(note);
  host.appendChild(bar);
}
const _g=id=>{ const e=$(id); return e?e.value:undefined; };
// The full sampler/penalty/prompt set read from the LLM tab controls (the "config" portable subset
// plus the launch params). Shared by saveLlm and "Save as config".
function readLlmSettings(){
  return {
    temperature:parseFloat(_g("llmTemp")), top_p:parseFloat(_g("llmTopP")),
    top_k:parseInt(_g("llmTopK"),10), min_p:parseFloat(_g("llmMinP")),
    repeat_penalty:parseFloat(_g("llmRepPen")), frequency_penalty:parseFloat(_g("llmFreqPen")),
    presence_penalty:parseFloat(_g("llmPresPen")), max_tokens:parseInt(_g("llmMaxTok"),10),
    seed:parseInt(_g("llmSeed"),10), system_prompt:_g("llmSysPrompt"),
    model:_g("llmModel"), context_size:parseInt(_g("llmCtx"),10),
    gpu_layers:parseInt(_g("llmNgl"),10), server_url:_g("llmUrl"), models_dir:_g("llmModelsDir"),
  };
}
function saveLlm(){ send({type:"saveLlamaSettings", settings:readLlmSettings()}); }
function onLlamaSaved(m){
  if(S.llm){ S.llm.settings=m.settings||S.llm.settings; if(m.models) S.llm.models=m.models; }
  // re-render so the model picker reflects the freshly scanned folder
  if(document.querySelector("#view-llm.active")) renderLlm();
  const note=$("llmSaveNote"); if(note) note.textContent=m.applied_live?"Saved — sampling applied live.":"Saved.";
}

// ---- saved LLM configs (portable sampler profiles) -------------------------
function configCard(s){
  const card=el("div","card"); card.appendChild(el("h2",null,"Configs"));
  card.appendChild(el("p","muted","Save the sampling settings + system prompt above as a named "
    +"profile and switch between them. The “default” config holds the standard llama.cpp parameters."));
  const loadRow=el("div","llm-actions");
  const sel=document.createElement("select"); sel.id="llmConfigSel"; sel.className="load-select";
  (S.llmConfigs||["default"]).forEach(n=>{ const o=document.createElement("option"); o.value=n; o.textContent=n; sel.appendChild(o); });
  const loadBtn=el("button","ghost","Load"); loadBtn.onclick=()=>{ const n=($("llmConfigSel")||{}).value; if(n) send({type:"loadLlmConfig",name:n}); };
  loadRow.appendChild(sel); loadRow.appendChild(loadBtn); card.appendChild(loadRow);
  const saveRow=el("div","llm-actions");
  const nm=document.createElement("input"); nm.id="llmConfigName"; nm.type="text"; nm.className="llm-url"; nm.placeholder="new config name";
  const saveBtn=el("button","primary","Save as config");
  saveBtn.onclick=()=>{ const n=($("llmConfigName")||{}).value.trim(); if(n) send({type:"saveLlmConfig",name:n,settings:readLlmSettings()}); };
  saveRow.appendChild(nm); saveRow.appendChild(saveBtn);
  const cnote=el("span","muted"); cnote.id="llmConfigNote"; saveRow.appendChild(cnote);
  card.appendChild(saveRow);
  return card;
}
function onLlmConfigs(m){ S.llmConfigs=m.configs||["default"];
  const sel=$("llmConfigSel"); if(sel){ const cur=sel.value; sel.innerHTML="";
    S.llmConfigs.forEach(n=>{ const o=document.createElement("option"); o.value=n; o.textContent=n; if(n===cur)o.selected=true; sel.appendChild(o); }); } }
function onLlmConfigSaved(m){ S.llmConfigs=m.configs||S.llmConfigs;
  const sel=$("llmConfigSel"); if(sel){ sel.innerHTML="";
    (S.llmConfigs||[]).forEach(n=>{ const o=document.createElement("option"); o.value=n; o.textContent=n; if(n===m.name)o.selected=true; sel.appendChild(o); }); }
  const note=$("llmConfigNote"); if(note) note.textContent=`Saved “${m.name}”.`;
  const nm=$("llmConfigName"); if(nm) nm.value=""; }
