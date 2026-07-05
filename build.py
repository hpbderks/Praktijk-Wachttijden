#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — enkel startpunt voor het wachttijden-dashboard
Gebruik: python3 build.py [--push]

Stappen:
  1. Lees dashboard_data_v3.json  (bron van waarheid)
  2. Genereer variant4c_final.html + index.html + dashboard_v3.html
  3. (--push) commit en push naar GitHub Pages

Lokale DB-workflow (optioneel, niet in git):
  Als je wachttijden.db bijwerkt, exporteer je eerst naar JSON:
    python3 export_db_to_json.py
  Dan pas: python3 build.py --push
"""
import json, shutil, subprocess, sys, os
from pathlib import Path
from datetime import date

HERE = Path(__file__).parent
JSON = HERE / 'dashboard_data_v3.json'
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyNCyAS4fb_IZ8NsLWvgaNEvZrfQGpbNeS3cFyBMGbIUAMsREglAPP5ZtVu3bGMhm-8/exec"

CAT_LABELS = {
    'angst_en_stemming':      'Angst & stemming',
    'complementaire_zorg':    'Complementaire zorg',
    'cultuur_en_religie':     'Cultuur & religie',
    'eetproblematiek':        'Eetproblematiek',
    'levensfase':             'Levensfase',
    'neurodiversiteit':       'Neurodiversiteit',
    'online_behandeling':     'Online behandeling',
    'relatie_en_seksualiteit':'Relatie & seksualiteit',
    'rouw_en_verlies':        'Rouw & verlies',
    'stress_en_burnout':      'Stress & burn-out',
    'trauma':                 'Trauma',
    'verslaving':             'Verslaving',
    'welzijn_en_herstel':     'Welzijn & herstel',
}

CITIES = [
    "'s-Hertogenbosch","Vught","Rosmalen","Zaltbommel","Oss","Eindhoven",
    "Sint-Michielsgestel","Berlicum","Amsterdam","Drunen","Vlijmen","Boxtel",
    "Zeist","Schijndel","Helvoirt","Veghel","Nuland","Waalwijk","Tilburg",
    "Nijmegen","Gorinchem","Utrecht","Tiel","Land van Altena","Gemonde",
]

def build_html(data, out_path, apps_url):
    import ast as _ast
    dj        = json.dumps(data, ensure_ascii=False)
    today_str = date.today().strftime('%d-%m-%Y')
    cat_opts  = '\n'.join(
        '<option value="{}">{}</option>'.format(k, v)
        for k, v in sorted(CAT_LABELS.items(), key=lambda x: x[1])
    )
    city_opts = '\n'.join(
        '<option value="{}">{}</option>'.format(c, c) for c in CITIES
    )
    fetch_line = "fetch('{}',{{method:'POST',mode:'no-cors',body:JSON.stringify({{naam:naam,praktijk:praktijk,opmerking:tekst,link:link}})}})".format(apps_url)
    cat_labels_js = json.dumps(CAT_LABELS, ensure_ascii=False)

    html = (
"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>Wachttijden dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
body{background:#fdf9f6;color:#2d1f1a;padding:28px;max-width:980px;margin:0 auto}
.header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:22px;flex-wrap:wrap}
h1{font-size:22px;font-weight:700;margin-bottom:2px;letter-spacing:-.3px}
.sub{font-size:12px;color:#9e7a6a}
.btn-suggest{background:#fff;color:#8b4513;border:1.5px solid #d4956a;border-radius:8px;padding:8px 14px;font-size:12.5px;font-weight:600;cursor:pointer;white-space:nowrap}
.btn-suggest:hover{background:#fff3e8}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:100;align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:#fff;border-radius:14px;padding:28px;width:100%;max-width:420px;box-shadow:0 8px 32px rgba(0,0,0,.16);position:relative}
.modal h2{font-size:16px;font-weight:700;margin-bottom:4px;color:#2d1f1a}
.modal-sub{font-size:12px;color:#9e7a6a;margin-bottom:18px;line-height:1.5}
.modal label{display:block;font-size:12px;font-weight:600;color:#4a3728;margin-bottom:3px;margin-top:12px}
.modal input,.modal textarea{width:100%;padding:8px 10px;border:1.5px solid #e8d8cf;border-radius:7px;font-size:13px;font-family:inherit}
.modal textarea{height:90px;resize:vertical}
.modal-actions{display:flex;gap:8px;margin-top:18px;justify-content:flex-end}
.btn-cancel{background:none;border:1.5px solid #e8d8cf;border-radius:7px;padding:7px 14px;font-size:13px;cursor:pointer;color:#4a3728}
.btn-submit{background:#8b4513;color:#fff;border:none;border-radius:7px;padding:7px 16px;font-size:13px;font-weight:600;cursor:pointer}
.btn-submit:hover{background:#7a3a10}
.btn-close{position:absolute;top:14px;right:16px;background:none;border:none;font-size:20px;cursor:pointer;color:#b08070;line-height:1}
.summary{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
.sc{flex:1 1 90px;background:#fff;border-radius:10px;padding:13px 8px;text-align:center;box-shadow:0 1px 3px rgba(139,90,60,.1);cursor:pointer;transition:box-shadow .15s,transform .1s;user-select:none}
.sc:hover{box-shadow:0 3px 10px rgba(139,90,60,.18);transform:translateY(-1px)}
.sc.active{box-shadow:0 0 0 2.5px #8b4513;transform:translateY(-1px)}
.sc-num{font-size:22px;font-weight:800;line-height:1.1}
.sc-lbl{font-size:9.5px;color:#b08070;margin-top:3px;text-transform:uppercase;letter-spacing:.4px;line-height:1.3}
.sc.groen .sc-num{color:#2e7d53}.sc.blauw .sc-num{color:#1a5f8a}
.sc.oranje .sc-num{color:#bf6520}.sc.rood .sc-num{color:#b52a2a}.sc.grijs .sc-num{color:#b08070}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px;align-items:center}
.filters input,.filters select{border:1.5px solid #e8d8cf;background:#fff;padding:8px 12px;border-radius:8px;font-size:13px;color:#2d1f1a;outline:none;cursor:pointer}
.filters input:focus,.filters select:focus{border-color:#8b4513}
.filters select{padding-right:28px;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%239e7a6a'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center}
.filter-row{display:flex;gap:8px;flex-wrap:wrap;width:100%;align-items:center}
#q{flex:1;min-width:160px}
.filters-reset{font-size:12px;color:#b08070;cursor:pointer;text-decoration:underline;white-space:nowrap;background:none;border:none;padding:0}
.filters-reset:hover{color:#8b4513}
#count{font-size:12px;color:#9e7a6a;margin-left:4px}
.list{display:flex;flex-direction:column;gap:8px}
.card{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(139,90,60,.08);overflow:hidden;transition:box-shadow .15s}
.card:hover{box-shadow:0 3px 14px rgba(139,90,60,.14)}
.card.open{box-shadow:0 4px 18px rgba(139,90,60,.16)}
.card-main{display:grid;grid-template-columns:10px 1fr auto;gap:0 14px;align-items:center;padding:15px 18px;cursor:pointer;user-select:none}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;align-self:start;margin-top:4px}
.dot-groen{background:#22c55e}.dot-blauw{background:#3b82f6}
.dot-oranje{background:#f97316}.dot-rood{background:#ef4444}.dot-grijs{background:#d1d5db}
.card-body{min-width:0}
.card-top{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-bottom:4px}
.card-naam{font-weight:700;font-size:14px;color:#2d1f1a}
.card-naam-link{font-weight:700;font-size:14px;color:#2d1f1a;text-decoration:none}
.card-naam-link:hover{color:#8b4513;text-decoration:underline}
.card-loc{font-size:11px;color:#9e7a6a}
.card-meta{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:5px}
.chip-intensity{display:inline-block;background:#fff3e8;color:#8b4513;font-size:10.5px;font-weight:700;padding:2px 7px;border-radius:4px;letter-spacing:.3px}
.chip-cat{display:inline-block;background:#f0f4ff;color:#3d5a99;font-size:10px;padding:2px 7px;border-radius:4px}
.chip-doel{display:inline-block;background:#f0fdf4;color:#166534;font-size:10px;padding:2px 7px;border-radius:4px;font-weight:600}
.tel{font-size:11px;color:#9e7a6a}
.card-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px}
.card-wt{text-align:right;display:flex;flex-direction:column;gap:4px;align-items:flex-end}
.wt-row{display:flex;align-items:center;gap:5px}
.wt-label{font-size:10px;color:#b08070;text-transform:uppercase;letter-spacing:.3px}
.chevron{font-size:11px;color:#c4956a;margin-top:6px;transition:transform .2s}
.card.open .chevron{transform:rotate(180deg)}
.badge{display:inline-block;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:700;white-space:nowrap}
.badge.groen{background:#f0fdf4;color:#166534}.badge.blauw{background:#eff6ff;color:#1e40af}
.badge.oranje{background:#fff7ed;color:#9a3412}.badge.rood{background:#fef2f2;color:#991b1b}
.badge.grijs{background:#f9fafb;color:#6b7280}
.badge-behandel{background:#f5f0ff;color:#5b21b6}
.card-detail{display:none;border-top:1.5px solid #f0e6df}
.card.open .card-detail{display:block}
.detail-wachttijd{font-size:13px;color:#4a3728;line-height:1.75;margin-top:12px;white-space:pre-wrap}
.detail-bron{margin-top:8px;font-size:11.5px}
.detail-bron a{color:#8b4513;text-decoration:none}
.detail-bron a:hover{text-decoration:underline}
.icon-sm{font-size:11px;margin-right:3px;opacity:.7}
.card-tabs{display:flex;padding:0 18px 0 42px;border-bottom:1.5px solid #f0e6df;margin:0}
.tab-btn{background:none;border:none;border-bottom:2.5px solid transparent;padding:8px 14px;font-size:12px;font-weight:600;color:#b08070;cursor:pointer;margin-bottom:-1.5px;transition:color .15s}
.tab-btn:hover{color:#8b4513}
.tab-btn.active{color:#8b4513;border-bottom-color:#8b4513}
.tab-panel{padding:10px 18px 14px 42px}
.tab-info{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;font-size:12.5px;align-items:baseline}
.ti-lbl{color:#b08070;font-weight:600;white-space:nowrap}
.ti-val{color:#4a3728;text-decoration:none;word-break:break-word}
a.ti-val:hover{color:#8b4513;text-decoration:underline}
.tab-verg{font-size:12.5px;color:#4a3728;line-height:1.75}
.detail-geen{font-size:12.5px;color:#b08070;font-style:italic;margin-top:8px}
.empty{text-align:center;padding:48px 0;color:#9e7a6a;font-size:14px}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>Wachttijden dashboard</h1>
    <p class="sub">Regio Den Bosch e.o. &middot; samenwijzeradvies.nl &middot; Bijgewerkt """ + today_str + """</p>
  </div>
  <button class="btn-suggest" onclick="document.getElementById('modal').classList.add('open')">&#9999; Suggestie indienen</button>
</div>
<div class="modal-overlay" id="modal" onclick="if(event.target===this)this.classList.remove('open')">
  <div class="modal">
    <button class="btn-close" onclick="document.getElementById('modal').classList.remove('open')">&times;</button>
    <h2>Suggestie indienen</h2>
    <p class="modal-sub">Klopt een wachttijd niet? Laat het weten &mdash; ik gebruik je suggestie om de data te verifieren en bij te werken.</p>
    <label>Naam (optioneel)</label><input type="text" id="sug-naam" placeholder="Jouw naam">
    <label>Praktijknaam *</label><input type="text" id="sug-praktijk" placeholder="Naam van de praktijk">
    <label>Wat klopt er niet? *</label><textarea id="sug-tekst" placeholder="bv. Wachttijd is nu 8 weken, of: aanmeldstop opgeheven..."></textarea>
    <label>Link / bron (optioneel)</label><input type="text" id="sug-link" placeholder="https://...">
    <div class="modal-actions">
      <button class="btn-cancel" onclick="document.getElementById('modal').classList.remove('open')">Annuleren</button>
      <button class="btn-submit" onclick="submitSuggestie()">Versturen</button>
    </div>
  </div>
</div>
<div class="summary" id="summary">
  <div class="sc groen" data-filter="gwc"><div class="sc-num" id="c-gwc"></div><div class="sc-lbl">Geen wachttijd</div></div>
  <div class="sc groen" data-filter="0-4"><div class="sc-num" id="c-04"></div><div class="sc-lbl">0&ndash;4 weken</div></div>
  <div class="sc blauw" data-filter="4-10"><div class="sc-num" id="c-410"></div><div class="sc-lbl">4&ndash;10 weken</div></div>
  <div class="sc oranje" data-filter="10-20"><div class="sc-num" id="c-1020"></div><div class="sc-lbl">10&ndash;20 weken</div></div>
  <div class="sc oranje" data-filter="20+"><div class="sc-num" id="c-20p"></div><div class="sc-lbl">20+ weken</div></div>
  <div class="sc rood" data-filter="stop"><div class="sc-num" id="c-stop"></div><div class="sc-lbl">Aanmeldstop</div></div>
  <div class="sc grijs" data-filter="unk"><div class="sc-num" id="c-unk"></div><div class="sc-lbl">Onbekend</div></div>
</div>
<div class="filters">
  <div class="filter-row">
    <input type="text" id="q" placeholder="Zoek op naam of locatie..." oninput="render()">
    <select id="fcat" onchange="render()">
      <option value="">Alle categorie&euml;n</option>
""" + cat_opts + """
    </select>
    <select id="fi" onchange="render()">
      <option value="">Alle intensiteiten</option>
      <option value="2">++ Basis GGZ</option>
      <option value="3">+++ Gespecialiseerd</option>
      <option value="4">++++ Hoog complex</option>
    </select>
    <select id="floc" onchange="render()">
      <option value="">Alle locaties</option>
""" + city_opts + """
    </select>
    <select id="fdoel" onchange="render()">
      <option value="">Alle doelgroepen</option>
      <option value="jeugd">Jeugd</option>
      <option value="volwassenen">Volwassenen</option>
      <option value="ouderen">Ouderen</option>
      <option value="alle leeftijden">Alle leeftijden</option>
    </select>
    <button class="filters-reset" onclick="resetFilters()">Wis filters</button>
    <span id="count"></span>
  </div>
</div>
<div class="list" id="list"></div>
<script>
var DATA=""" + dj + """;
var activeSc=null;
var CAT_LABELS=""" + cat_labels_js + """;
document.getElementById('c-gwc').textContent=DATA.filter(function(r){return r.status==='geen_wachttijd_concept'||r.status==='geen_wachtlijst';}).length;
document.getElementById('c-04').textContent=DATA.filter(function(r){return r.status==='bekend'&&r.weken_sort!==null&&r.weken_sort<=4;}).length;
document.getElementById('c-410').textContent=DATA.filter(function(r){return r.status==='bekend'&&r.weken_sort!==null&&r.weken_sort>4&&r.weken_sort<=10;}).length;
document.getElementById('c-1020').textContent=DATA.filter(function(r){return r.status==='bekend'&&r.weken_sort!==null&&r.weken_sort>10&&r.weken_sort<=20;}).length;
document.getElementById('c-20p').textContent=DATA.filter(function(r){return r.status==='bekend'&&r.weken_sort!==null&&r.weken_sort>20;}).length;
document.getElementById('c-stop').textContent=DATA.filter(function(r){return r.status==='aanmeldstop';}).length;
document.getElementById('c-unk').textContent=DATA.filter(function(r){return r.status==='onbekend';}).length;
document.querySelectorAll('.sc').forEach(function(sc){
  sc.addEventListener('click',function(){
    var f=sc.dataset.filter;
    if(activeSc===f){activeSc=null;sc.classList.remove('active');}
    else{document.querySelectorAll('.sc').forEach(function(s){s.classList.remove('active');});activeSc=f;sc.classList.add('active');}
    render();
  });
});
function resetFilters(){
  document.getElementById('q').value='';document.getElementById('fcat').value='';
  document.getElementById('fi').value='';document.getElementById('floc').value='';
  activeSc=null;document.querySelectorAll('.sc').forEach(function(s){s.classList.remove('active');});render();
}
function rank(r){
  var st=r.status,ws=r.weken_sort;
  if(st==='geen_wachttijd_concept')return -2;if(st==='geen_wachtlijst')return -1;
  if(st==='aanmeldstop')return 9000;if(st==='onbekend')return 9001;
  if(ws===null||ws===undefined)return 8999;
  if(r.aanmeld_weken){var m=String(r.aanmeld_weken).match(/[\\d.,]+/);if(m)return parseFloat(m[0].replace(',','.'));}
  return ws;
}
function cls(r){
  var ws=r.weken_sort,st=r.status;
  if(st==='geen_wachttijd_concept'||st==='geen_wachtlijst')return 'groen';
  if(st==='aanmeldstop')return 'rood';if(st==='onbekend')return 'grijs';
  if(ws===null||ws===undefined)return 'grijs';
  return ws<=4?'groen':ws<=10?'blauw':ws<=20?'oranje':'rood';
}
function intakeLbl(r){
  var aw=r.aanmeld_weken,ws=r.weken_sort,st=r.status;
  if(st==='geen_wachttijd_concept')return 'N.v.t.';if(st==='geen_wachtlijst')return 'Geen wachtlijst';
  if(st==='aanmeldstop')return 'Aanmeldstop';if(st==='onbekend')return 'Onbekend';
  if(aw)return aw+' wk';if(ws!==null&&ws!==undefined)return ws+' wk';return '?';
}
function behandelTotaal(r){
  if(!r.behandel_weken)return null;
  var bm=String(r.behandel_weken).match(/^(\\d+)(?:[-\\u2013](\\d+))?/);if(!bm)return null;
  var bmMin=parseInt(bm[1]),bmMax=bm[2]?parseInt(bm[2]):bmMin;
  var aStr=String(r.aanmeld_weken||'');
  var am=aStr.match(/^(\\d+)(?:[-\\u2013](\\d+))?/);var amMin,amMax;
  if(am){amMin=parseInt(am[1]);amMax=am[2]?parseInt(am[2]):amMin;}
  else{var ws=r.weken_sort||0;amMin=amMax=ws;}
  var tMin=amMin+bmMin,tMax=amMax+bmMax;
  return (tMin===tMax?String(tMin):tMin+'-'+tMax)+' wk';
}
function matchesSc(r){
  if(!activeSc)return true;var ws=r.weken_sort,st=r.status;
  if(activeSc==='gwc')return st==='geen_wachttijd_concept'||st==='geen_wachtlijst';
  if(activeSc==='0-4')return st==='bekend'&&ws!==null&&ws<=4;
  if(activeSc==='4-10')return st==='bekend'&&ws!==null&&ws>4&&ws<=10;
  if(activeSc==='10-20')return st==='bekend'&&ws!==null&&ws>10&&ws<=20;
  if(activeSc==='20+')return st==='bekend'&&ws!==null&&ws>20;
  if(activeSc==='stop')return st==='aanmeldstop';if(activeSc==='unk')return st==='onbekend';return true;
}
function esc(s){return s?String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'):''; }
function render(){
  var q=document.getElementById('q').value.toLowerCase();
  var fcat=document.getElementById('fcat').value;var fi=document.getElementById('fi').value;
  var floc=document.getElementById('floc').value;
    var fdoel=document.getElementById('fdoel').value;
  var rows=DATA.filter(function(r){
    if(q&&!(r.naam+' '+(r.locatie_norm||r.locatie||'')).toLowerCase().includes(q))return false;
    if(fcat&&!(r.cats||[]).includes(fcat))return false;
    if(fi&&String(r.level)!==fi)return false;
    if(floc&&(r.locatie_norm||r.locatie)!==floc)return false;
    if(fdoel&&r.doelgroep!==fdoel)return false;
    if(!matchesSc(r))return false;return true;
  });
  rows.sort(function(a,b){return rank(a)-rank(b);});
  document.getElementById('count').textContent=rows.length+' van '+DATA.length+' praktijken';
  if(!rows.length){document.getElementById('list').innerHTML='<div class="empty">Geen praktijken gevonden</div>';return;}
  document.getElementById('list').innerHTML=rows.map(function(r){
    var c=cls(r);
    var naamHtml=r.website?'<a class="card-naam-link" href="'+esc(r.website)+'" target="_blank" onclick="event.stopPropagation()">'+esc(r.naam)+'</a>':'<span class="card-naam">'+esc(r.naam)+'</span>';
    var intakeHtml='<div class="wt-row"><span class="wt-label">Intake</span><span class="badge '+c+'">'+intakeLbl(r)+'</span></div>';
    var tot=behandelTotaal(r);
    var bHtml=tot?'<div class="wt-row"><span class="wt-label">Behandeling</span><span class="badge badge-behandel">'+tot+'</span></div>':'';
    var intLabel=r.level==2?'++':r.level==3?'+++':r.level==4?'++++':'';
    var cats=(r.cats||[]).slice(0,2).map(function(k){return '<span class="chip-cat">'+esc(CAT_LABELS[k]||k)+'</span>';}).join('');
    var hasDetail=true;
    var detailHtml='<div class="card-detail">'
      +'<div class="card-tabs"><button class="tab-btn active" data-tab="wacht">Wachttijden</button><button class="tab-btn" data-tab="alg">Algemeen</button><button class="tab-btn" data-tab="verg">Vergoeding</button></div>'
      +'<div class="tab-panel" data-tab="wacht">'
      +(r.wachttijd?'<div class="detail-wachttijd">'+esc(r.wachttijd)+'</div>':'<p class="detail-geen">Geen toelichting beschikbaar.</p>')
      +(r.bron?'<div class="detail-bron">Bron: <a href="'+esc(r.bron)+'" target="_blank">'+esc(r.bron)+'</a></div>':'')
      +'</div>'
      +'<div class="tab-panel" style="display:none" data-tab="alg"><div class="tab-info">'
      +(r.telefoon?'<span class="ti-lbl">Telefoon</span><a class="ti-val" href="tel:'+esc(r.telefoon)+'">'+esc(r.telefoon)+'</a>':'')
      +(r.email?'<span class="ti-lbl">E-mail</span><a class="ti-val" href="mailto:'+esc(r.email)+'">'+esc(r.email)+'</a>':'')
      +(r.website?'<span class="ti-lbl">Website</span><a class="ti-val" href="'+esc(r.website)+'" target="_blank">'+esc(r.website)+'</a>':'')
      +((r.locatie_norm||r.locatie)?'<span class="ti-lbl">Locatie</span><span class="ti-val">'+esc(r.locatie_norm||r.locatie)+'</span>':'')
      +(r.doelgroep?'<span class="ti-lbl">Doelgroep</span><span class="ti-val">'+esc(r.doelgroep)+'</span>':'')
      +((r.cats&&r.cats.length)?'<span class="ti-lbl">Specialisaties</span><span class="ti-val">'+r.cats.map(function(k){return CAT_LABELS[k]||k;}).join(', ')+'</span>':'')
      +'</div></div>'
      +'<div class="tab-panel" style="display:none" data-tab="verg"><div class="tab-verg">GGZ-behandelingen worden vergoed vanuit de <b>basisverzekering</b>, mits er een geldige verwijsbrief van de huisarts is. Het eigen risico is van toepassing.<br><br>Neem voor specifieke informatie over vergoedingen contact op met de praktijk of je zorgverzekeraar.</div></div>'
      +'</div>';
    return '<div class="card" onclick="toggleCard(this,event)"><div class="card-main"><div class="dot dot-'+c+'"></div><div class="card-body"><div class="card-top">'+naamHtml+'<span class="card-loc"><span class="icon-sm">&#x1F4CD;</span>'+esc(r.locatie_norm||r.locatie||'')+'</span>'+(r.telefoon?'<span class="card-loc"><span class="icon-sm">&#x1F4DE;</span>'+esc(r.telefoon)+'</span>':'')+'</div><div class="card-meta">'+(intLabel?'<span class="chip-intensity">'+intLabel+'</span>':'')+cats+(r.doelgroep?'<span class="chip-doel">'+esc(r.doelgroep)+'</span>':'')+'</div></div><div class="card-right"><div class="card-wt">'+intakeHtml+bHtml+'</div>'+(hasDetail?'<div class="chevron">&#9660;</div>':'')+'</div></div>'+detailHtml+'</div>';
  }).join('');
}
function toggleCard(card,event){if(event&&event.target.closest('.card-detail'))return;card.classList.toggle('open');}
document.addEventListener('click',function(e){
  var btn=e.target.closest('.tab-btn');if(!btn)return;
  e.stopPropagation();
  var d=btn.closest('.card-detail');
  d.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active');});
  d.querySelectorAll('.tab-panel').forEach(function(p){p.style.display='none';});
  btn.classList.add('active');
  d.querySelector('.tab-panel[data-tab="'+btn.dataset.tab+'"]').style.display='block';
});
render();
function submitSuggestie(){
  var naam=document.getElementById('sug-naam').value.trim();
  var praktijk=document.getElementById('sug-praktijk').value.trim();
  var tekst=document.getElementById('sug-tekst').value.trim();
  var link=document.getElementById('sug-link').value.trim();
  if(!praktijk||!tekst){alert('Vul minimaal de praktijknaam en een toelichting in.');return;}
  var btn=document.querySelector('.btn-submit');btn.disabled=true;btn.textContent='Versturen...';
  """ + fetch_line + """
  .then(function(){
    btn.disabled=false;btn.textContent='Versturen';
    document.getElementById('modal').classList.remove('open');
    ['sug-naam','sug-praktijk','sug-tekst','sug-link'].forEach(function(id){document.getElementById(id).value='';});
    alert('Bedankt! Je suggestie is ontvangen.');
  }).catch(function(){btn.disabled=false;btn.textContent='Versturen';alert('Er ging iets mis. Probeer het later opnieuw.');});
}
</script>
</body></html>"""
    )
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("[2] Dashboard geschreven: {} ({} KB)".format(out_path.name, len(html.encode())//1024))

def push(here):
    cfg = here / '.github_config'
    if not cfg.exists():
        print("[!] .github_config niet gevonden, push overgeslagen"); return
    token = None
    with open(cfg) as f:
        for line in f:
            if line.startswith('GITHUB_TOKEN='):
                token = line.strip().split('=', 1)[1]
    if not token:
        print("[!] GITHUB_TOKEN niet gevonden"); return
    import tempfile
    repo_url = "https://hpbderks:{}@github.com/hpbderks/Praktijk-Wachttijden.git".format(token)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['git', 'clone', '--depth=1', repo_url, tmp], check=True, capture_output=True)
        for f in ['variant4c_final.html', 'index.html', 'dashboard_v3.html',
                  'dashboard_data_v3.json', 'build.py', 'export_db_to_json.py']:
            src = here / f
            if src.exists():
                shutil.copy(src, os.path.join(tmp, f))
        gi = here / '.gitignore_template'  # already written
        subprocess.run(['git', '-C', tmp, 'config', 'user.email', 'hpbderks@gmail.com'], check=True)
        subprocess.run(['git', '-C', tmp, 'config', 'user.name', 'Huub'], check=True)
        subprocess.run(['git', '-C', tmp, 'add',
                        'variant4c_final.html', 'index.html', 'dashboard_v3.html',
                        'dashboard_data_v3.json', 'build.py', 'export_db_to_json.py'], check=True)
        result = subprocess.run(['git', '-C', tmp, 'commit', '-m',
                                 'Dashboard update {}'.format(date.today())],
                                capture_output=True)
        if b'nothing to commit' in result.stdout + result.stderr:
            print("[3] Geen wijzigingen om te pushen"); return
        subprocess.run(['git', '-C', tmp, 'push', 'origin', 'HEAD'], check=True, capture_output=True)
        print("[3] Gepusht naar GitHub Pages")

if __name__ == '__main__':
    do_push = '--push' in sys.argv
    if not JSON.exists():
        print("[!] {} niet gevonden".format(JSON)); sys.exit(1)
    with open(JSON, encoding='utf-8') as f:
        data = json.load(f)
    print("[1] Geladen: {} praktijken uit {}".format(len(data), JSON.name))
    build_html(data, HERE / 'variant4c_final.html', APPS_SCRIPT_URL)
    for alias in ['index.html', 'dashboard_v3.html']:
        shutil.copy(HERE / 'variant4c_final.html', HERE / alias)
        print("    -> {}".format(alias))
    if do_push:
        push(HERE)
    else:
        print("[i] Gebruik --push om naar GitHub te deployen")
