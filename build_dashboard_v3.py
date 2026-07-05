# -*- coding: utf-8 -*-
"""Build the multi-category dashboard HTML (v3, ALL 13 categories) from dashboard_data_v3.json."""
import json, re
from parse_split import parse_split

def _parse_weken_range(text):
    """Extract a week-range string (e.g. '10-12') from free-text wachttijd.
    Returns '10-12' if found and None otherwise. Only matches explicit
    week-ranges (not month-ranges). The caller should do a consistency
    check against weken_sort before applying."""
    if not text:
        return None
    t = text.lower()
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*(?:weken|weeks|wk)\b", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(\d+)\s+tot\s+(\d+)\s*(?:weken|weeks|wk)\b", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None

with open("dashboard_data_v3.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)


def _num_to_str(n):
    """Format a manually-curated SPLIT_OVERRIDES number the same way the
    old JS fmtSplit() did (comma decimal), so all aanmeld/behandel values
    -- whether from SPLIT_OVERRIDES or from parse_split() -- end up as
    plain display-ready strings (or None) by the time they reach the JS.
    Also passes range strings (e.g. "2-8") through unchanged."""
    if n is None:
        return None
    if isinstance(n, str):
        return n  # already a formatted range string, e.g. "2-8" or "25-30"
    return str(int(n)) if float(n) == int(n) else str(n).replace(".", ",")

CAT_LABELS = {
    "welzijn_en_herstel": "Welzijn & herstel",
    "rouw_en_verlies": "Rouw & verlies",
    "stress_en_burnout": "Stress & burnout",
    "relatie_en_seksualiteit": "Relatie, seksualiteit en gender",
    "online_behandeling": "Online behandeling",
    "angst_en_stemming": "Angst & stemming",
    "trauma": "Trauma",
    "neurodiversiteit": "Neurodiversiteit",
    "cultuur_en_religie": "Cultuur & religie",
    "verslaving": "Verslaving",
    "levensfase": "Levensfase",
    "eetproblematiek": "Eetproblematiek",
    "complementaire_zorg": "Complementaire zorg",
}
# All 13 categories now fully mapped.
MAPPED = list(CAT_LABELS.keys())
CAT_ORDER = ["trauma", "welzijn_en_herstel", "angst_en_stemming", "stress_en_burnout",
             "rouw_en_verlies", "relatie_en_seksualiteit", "cultuur_en_religie",
             "neurodiversiteit", "verslaving", "eetproblematiek", "levensfase",
             "online_behandeling", "complementaire_zorg"]

# Aanmeldwachttijd (tot intake) vs behandelwachttijd (intake -> start behandeling),
# alleen ingevuld waar de praktijk dit zelf expliciet als twee losse cijfers (of
# ranges, bv. "2-8") vermeldt (nooit afgeleid/geschat uit een gecombineerd of
# ambigu cijfer). SPLIT_OVERRIDES = handmatig nagekeken waarden (~25 trauma-
# rijen, enkelvoudige cijfers, leidend boven de automatische parser hieronder).
# Voor alle overige rijen wordt parse_split() gebruikt: een conservatieve
# tekst-parser die ook ranges en maanden->weken (x4) ondersteunt, en alleen
# een waarde teruggeeft als aanmeld- en behandelwachttijd elk precies een
# keer ondubbelzinnig in de wachttijd-tekst voorkomen.
SPLIT_OVERRIDES = {
    "Willemien Jobsen": (2, None),
    "Max Ernst": (35, 10),
    "Eerstelijnspsychologen Den Bosch": (20, None),
    "SmuldersPsychologie": (16, 0),
    "Yellow Psychotherapie": (None, 2),
    "EMDR psycholoog Vught": (1.5, 1),
    "Femke Arnoldussen. GZ-psychologie & Coaching": (11, 4.5),
    "Licht inZicht": (26, 2),
    "Noor de Spiegoloog": (13, None),
    "Christy Donkers": (0, None),
    "Reinier van Arkel": (39, 9),
    "Innova GGZ": (4, None),
    "de Viersprong": (None, 16),
    "De Hemisfeer": (27, None),
    "Psychotherapie Steenbeek": (1, None),
    "Changes GGZ": (2, None),
    "GGZ Breburg": (42, 5),
    "Psychotrauma Centrum Nederland": (17, 11),
    "Psytrec": (3, "2-8"),  # intake 2-4 wk (sort=3), behandeling 2-8 wk (tekst)
    "Psychotherapie Praktijk Truijens": (2.5, None),
    "GGZ Momentum": ("25-30", "6-8"),  # aanmeld 25-30 wk, behandel 6-8 wk (ambulant individueel)
    "Levura GGZ": (16, None),
    "Expertisecentrum Groen": (0, None),
    "Saleem GGZ": (15, None),
    "Walboomers Psychologie": (10, 0),
}

split_auto_count = 0
for r in DATA:
    if r["naam"] in SPLIT_OVERRIDES:
        a, b = SPLIT_OVERRIDES[r["naam"]]
        a, b = _num_to_str(a), _num_to_str(b)
    else:
        a, b = parse_split(r.get("wachttijd", ""))
        if a or b:
            split_auto_count += 1
    r["aanmeld_weken"] = a
    r["behandel_weken"] = b
    r["categorieen_label"] = ", ".join(CAT_LABELS.get(c, c) for c in r["categorieen"])

# Post-pass: for rows where aanmeld_weken is still None, try to extract
# a week-range from the wachttijd text. Only apply when status is known
# (not "onbekend") and the extracted range is consistent with weken_sort.
range_auto_count = 0
for r in DATA:
    if r["aanmeld_weken"] is None and r.get("status") != "onbekend":
        rng = _parse_weken_range(r.get("wachttijd", ""))
        if rng:
            lo, hi = (int(x) for x in rng.split("-"))
            ws = r.get("weken_sort")
            if ws is not None and lo <= float(ws) <= hi:
                r["aanmeld_weken"] = rng
                range_auto_count += 1

print("aanmeld/behandel split: %d handmatig (SPLIT_OVERRIDES) + %d automatisch (parse_split) + %d ranges uit tekst" % (
    len(SPLIT_OVERRIDES), split_auto_count, range_auto_count))

data_json = json.dumps(DATA, ensure_ascii=False)
cat_labels_json = json.dumps(CAT_LABELS, ensure_ascii=False)
mapped_json = json.dumps(MAPPED, ensure_ascii=False)
n_total = len(DATA)
cat_counts = {c: sum(1 for r in DATA if c in r["categorieen"]) for c in CAT_ORDER}
mapped_str = "alle 13 categorie&euml;n van samenwijzeradvies.nl (%d praktijken in totaal)" % n_total

cat_options_html = "\n".join(
    '      <option value="%s">%s (%d)</option>' % (c, CAT_LABELS[c], cat_counts[c])
    for c in CAT_ORDER
)

HTML = """<!DOCTYPE html>
<script type="application/json" id="cowork-artifact-meta">
{{
  "name": "Praktijken Wachttijden Dashboard",
  "schemaVersion": 1,
  "description": "Overzicht van praktijken/organisaties (regio Den Bosch e.o.) per categorie van samenwijzeradvies.nl, met zorgintensiteit, telefoonnummer, website, actuele wachttijd (genormaliseerd naar weken, met bronlink en hover-toelichting), locatie en categorie. Filterbaar en sorteerbaar, inclusief categorie-switcher voor alle 13 categorie&euml;n. Toont datum van laatste actualisatie van de wachttijden."
}}
</script>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>Praktijken &mdash; wachttijden dashboard</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ margin: 0; padding: 16px; background: #ffffff; }}
</style>
</head>
<body>
<div id="root">
<style>
  #root, #root * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; }}
  #root {{ color: #1f2430; background: #ffffff; }}
  .twd-header {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 14px; }}
  .twd-title {{ font-size: 19px; font-weight: 700; margin: 0 0 4px 0; color: #1f2430; }}
  .twd-sub {{ font-size: 12.5px; color: #6b7280; margin: 0; }}
  .twd-btn {{ background: #2E5C8A; color: #fff; border: none; border-radius: 7px; padding: 9px 16px; font-size: 13.5px; font-weight: 600; cursor: pointer; white-space: nowrap; }}
  .twd-btn:hover {{ background: #244a6e; }}
  .twd-btn:disabled {{ background: #9aa7b5; cursor: default; }}
  .twd-refresh-hint {{ background: #eaf0fb; color: #2E5C8A; border: 1px solid #d3e0f5; border-radius: 7px; padding: 9px 14px; font-size: 12.5px; line-height: 1.5; max-width: 280px; }}
  .twd-refresh-hint b {{ display: block; margin-bottom: 2px; }}
  .twd-filters {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; padding: 12px; background: #f6f7f9; border-radius: 9px; }}
  .twd-filters label {{ font-size: 11px; color: #6b7280; font-weight: 600; display: block; margin-bottom: 3px; }}
  .twd-filters input[type=text], .twd-filters select {{ font-size: 13px; padding: 6px 8px; border: 1px solid #d6dae0; border-radius: 6px; background: #fff; min-width: 140px; }}
  .twd-count {{ font-size: 12px; color: #6b7280; margin: 0 0 8px 2px; }}
  table.twd-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .twd-table th {{ text-align: left; padding: 8px 10px; background: #2E5C8A; color: #fff; font-weight: 600; cursor: pointer; user-select: none; white-space: nowrap; position: sticky; top: 0; }}
  .twd-table th .arrow {{ opacity: 0.7; font-size: 11px; margin-left: 4px; }}
  .twd-table td {{ padding: 8px 10px; border-bottom: 1px solid #ebedf0; vertical-align: top; }}
  .twd-table tr:hover td {{ background: #f9fafb; }}
  .twd-table-wrap {{ max-height: 600px; overflow: auto; border: 1px solid #ebedf0; border-radius: 8px; }}
  .twd-badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; white-space: nowrap; position: relative; }}
  .twd-badge[data-tip] {{ cursor: help; }}
  .twd-badge[data-tip]:hover::after {{
    content: attr(data-tip); position: absolute; left: 50%; bottom: 140%; transform: translateX(-50%);
    background: #1f2430; color: #fff; padding: 8px 10px; border-radius: 6px;
    font-size: 11.5px; font-weight: 400; white-space: normal; width: 280px;
    line-height: 1.4; z-index: 20; box-shadow: 0 4px 12px rgba(0,0,0,.2);
  }}
  .twd-badge[data-tip]:hover::before {{
    content: ''; position: absolute; left: 50%; bottom: 118%; transform: translateX(-50%);
    border: 5px solid transparent; border-top-color: #1f2430; z-index: 20;
  }}
  .badge-bekend {{ background: #e3f6e8; color: #1d7a3e; }}
  .badge-geen_wachtlijst {{ background: #e3f6e8; color: #1d7a3e; }}
  .badge-aanmeldstop {{ background: #fde8e8; color: #b42318; }}
  .badge-onbekend {{ background: #f1f2f4; color: #6b7280; }}
  .badge-laat {{ background: #fff3e0; color: #c45000; }}
  .badge-geen_wachttijd_concept {{ background: #e3f6e8; color: #1d7a3e; }}
  .twd-link {{ color: #2E5C8A; text-decoration: none; font-size: 12px; margin-left: 6px; white-space: nowrap; }}
  .twd-link:hover {{ text-decoration: underline; }}
  .twd-website {{ color: #2E5C8A; text-decoration: none; font-weight: 600; }}
  .twd-website:hover {{ text-decoration: underline; }}
  .twd-wt-cell {{ display: flex; align-items: center; gap: 6px; flex-wrap: nowrap; }}
  .twd-status-msg {{ font-size: 12.5px; color: #6b7280; margin: 0 0 10px 2px; min-height: 16px; }}
  .twd-info {{ display: inline-flex; align-items: center; justify-content: center; width: 15px; height: 15px; border-radius: 50%; background: #e1e6ec; color: #51607a; font-size: 10.5px; font-style: normal; text-decoration: none; cursor: default; position: relative; flex-shrink: 0; }}
  .twd-info:hover::after {{
    content: attr(data-tip);
    position: absolute; left: 50%; bottom: 140%; transform: translateX(-50%);
    background: #1f2430; color: #fff; padding: 8px 10px; border-radius: 6px;
    font-size: 11.5px; font-weight: 400; white-space: normal; width: 280px;
    line-height: 1.4; z-index: 20; box-shadow: 0 4px 12px rgba(0,0,0,.2);
  }}
  .twd-info:hover::before {{
    content: ""; position: absolute; left: 50%; bottom: 118%; transform: translateX(-50%);
    border: 5px solid transparent; border-top-color: #1f2430; z-index: 20;
  }}
  .twd-cat-chip {{ display: inline-block; padding: 1px 7px; border-radius: 999px; font-size: 10.5px; font-weight: 600; white-space: nowrap; background: #eaf0fb; color: #2E5C8A; margin: 1px 2px 1px 0; }}
  .resize-handle {{ position: absolute; right: 0; top: 0; width: 5px; height: 100%; cursor: col-resize; user-select: none; z-index: 1; }}
  .resize-handle:hover, .resize-handle.resizing {{ background: rgba(255,255,255,0.35); border-radius: 2px; }}
  .twd-table th {{ position: relative; }}
  .twd-disclaimer {{ font-size: 11px; color: #8a93a3; margin: 14px 2px 0 2px; line-height: 1.5; border-top: 1px solid #ebedf0; padding-top: 10px; }}
  .twd-summary {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }}
  .twd-summary-card {{ flex: 1 1 100px; min-width: 90px; max-width: 200px; background: #f6f7f9; border: 1.5px solid #ebedf0; border-radius: 9px; padding: 10px 12px 8px; cursor: pointer; transition: border-color 0.15s, background 0.15s; text-align: center; }}
  .twd-summary-card:hover {{ border-color: #2E5C8A; background: #eaf0fb; }}
  .twd-summary-card.active {{ border-color: #2E5C8A; background: #eaf0fb; }}
  .twd-summary-card .sc-num {{ font-size: 22px; font-weight: 700; line-height: 1.1; }}
  .twd-summary-card .sc-lbl {{ font-size: 10.5px; font-weight: 600; color: #6b7280; margin-top: 3px; line-height: 1.3; }}
  .sc-groen .sc-num {{ color: #1d7a3e; }}
  .sc-blauw .sc-num {{ color: #2E5C8A; }}
  .sc-oranje .sc-num {{ color: #c45000; }}
  .sc-rood .sc-num {{ color: #b42318; }}
  .sc-grijs .sc-num {{ color: #6b7280; }}
  .twd-suggest-btn {{ background: #fff; color: #2E5C8A; border: 1.5px solid #2E5C8A; border-radius: 7px; padding: 7px 14px; font-size: 12.5px; font-weight: 600; cursor: pointer; white-space: nowrap; }}
  .twd-suggest-btn:hover {{ background: #eaf0fb; }}
  .twd-modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 100; align-items: center; justify-content: center; }}
  .twd-modal-overlay.open {{ display: flex; }}
  .twd-modal {{ background: #fff; border-radius: 12px; padding: 28px 28px 22px; width: 100%; max-width: 440px; box-shadow: 0 8px 32px rgba(0,0,0,0.18); position: relative; }}
  .twd-modal h2 {{ margin: 0 0 6px; font-size: 16px; color: #1f2430; }}
  .twd-modal p.twd-modal-sub {{ margin: 0 0 18px; font-size: 12.5px; color: #6b7280; line-height: 1.5; }}
  .twd-modal label {{ display: block; font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 3px; margin-top: 12px; }}
  .twd-modal input, .twd-modal textarea {{ width: 100%; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 7px; font-size: 13px; font-family: inherit; box-sizing: border-box; }}
  .twd-modal textarea {{ height: 90px; resize: vertical; }}
  .twd-modal-actions {{ display: flex; gap: 10px; margin-top: 20px; justify-content: flex-end; }}
  .twd-modal-cancel {{ background: none; border: 1.5px solid #d1d5db; border-radius: 7px; padding: 8px 16px; font-size: 13px; cursor: pointer; color: #374151; }}
  .twd-modal-submit {{ background: #2E5C8A; color: #fff; border: none; border-radius: 7px; padding: 8px 18px; font-size: 13px; font-weight: 600; cursor: pointer; }}
  .twd-modal-submit:hover {{ background: #244a6e; }}
  .twd-modal-close {{ position: absolute; top: 14px; right: 16px; background: none; border: none; font-size: 20px; cursor: pointer; color: #9ca3af; line-height: 1; }}
</style>

<div class="twd-header">
  <div>
    <p class="twd-title">Praktijken &mdash; wachttijden dashboard</p>
    <p class="twd-sub">Regio Den Bosch e.o. &middot; samenwijzeradvies.nl &middot; <span id="twd-last-updated">29-06-2026</span></p>
  </div>
  <div style="display:flex; flex-direction:column; align-items:flex-end; gap:8px;">
    <div class="twd-refresh-hint">
      <b>Laatst geactualiseerd</b>
      02-07-2026
    </div>
    <button class="twd-suggest-btn" onclick="document.getElementById('twd-suggest-overlay').classList.add('open')">✏️ Suggestie indienen</button>
  </div>
</div>

<!-- Suggestie modal -->
<div class="twd-modal-overlay" id="twd-suggest-overlay" onclick="if(event.target===this)this.classList.remove('open')">
  <div class="twd-modal">
    <button class="twd-modal-close" onclick="document.getElementById('twd-suggest-overlay').classList.remove('open')">&times;</button>
    <h2>Suggestie indienen</h2>
    <p class="twd-modal-sub">Klopt een wachttijd niet? Laat het weten — ik gebruik je suggestie om de data te verifiëren en bij te werken.</p>
    <label>Naam (optioneel)</label>
    <input type="text" id="sug-naam" placeholder="Jouw naam">
    <label>Praktijknaam *</label>
    <input type="text" id="sug-praktijk" placeholder="Naam van de praktijk">
    <label>Wat klopt er niet / wat wil je doorgeven? *</label>
    <textarea id="sug-tekst" placeholder="bv. Wachttijd is nu 8 weken, of: aanmeldstop opgeheven..."></textarea>
    <label>Link / bron (optioneel)</label>
    <input type="text" id="sug-link" placeholder="https://...">
    <div class="twd-modal-actions">
      <button class="twd-modal-cancel" onclick="document.getElementById('twd-suggest-overlay').classList.remove('open')">Annuleren</button>
      <button class="twd-modal-submit" onclick="submitSuggestie()">Versturen</button>
    </div>
  </div>
</div>

<!-- Samenvatting -->
<div class="twd-summary" id="twd-summary"></div>

<div class="twd-filters">
  <div>
    <label>Zoeken (naam / locatie / website / email)</label>
    <input type="text" id="f-search" placeholder="bv. EMDR, Vught...">
  </div>
  <div>
    <label>Categorie</label>
    <select id="f-categorie">
      <option value="">Alle categorie&euml;n ({n_total})</option>
{cat_options_html}
    </select>
  </div>
  <div>
    <label>Zorgintensiteit</label>
    <select id="f-level">
      <option value="">Alle</option>
      <option value="2">++</option>
      <option value="3">+++</option>
      <option value="4">++++</option>
    </select>
  </div>
  <div>
    <label>Status</label>
    <select id="f-status">
      <option value="">Alle</option>
      <option value="bekend">Bekend</option>
      <option value="geen_wachtlijst">Geen wachtlijst</option>
      <option value="aanmeldstop">Aanmeldstop</option>
      <option value="geen_wachttijd_concept">Geen wachttijd-concept</option>
      <option value="onbekend">Onbekend</option>
    </select>
  </div>
  <div>
    <label>Locatie</label>
    <select id="f-locatie"><option value="">Alle</option></select>
  </div>
</div>

<p class="twd-count" id="twd-count"></p>

<div class="twd-table-wrap">
<table class="twd-table">
  <thead>
    <tr>
      <th data-key="naam">Naam<span class="arrow"></span><div class="resize-handle"></div></th>
      <th data-key="level">Zorgintensiteit<span class="arrow"></span><div class="resize-handle"></div></th>
      <th data-key="weken_sort">Wachttijd voor intake<span class="arrow"></span><div class="resize-handle"></div></th>
      <th data-key="behandel_weken">Behandelwachttijd<span class="arrow"></span><div class="resize-handle"></div></th>
      <th data-key="telefoon">Telefoonnummer<span class="arrow"></span><div class="resize-handle"></div></th>
      <th data-key="email">Email<span class="arrow"></span><div class="resize-handle"></div></th>
      <th data-key="locatie">Locatie<span class="arrow"></span><div class="resize-handle"></div></th>
      <th data-key="categorieen_label">Categorie&euml;n<span class="arrow"></span><div class="resize-handle"></div></th>
    </tr>
  </thead>
  <tbody id="twd-tbody"></tbody>
</table>
</div>

<p class="twd-disclaimer">
  Dit dashboard toont indicatieve wachttijden, gebaseerd op informatie van de website van elke praktijk (of een gerichte zoekopdracht als de website geen JS-vrije inhoud bood) op het moment van de laatste actualisatie (zie datum hierboven). Wachttijden kunnen wijzigen en kunnen per zorgverzekeraar of behandelaar verschillen. Neem altijd zelf contact op met de praktijk voor de actuele wachttijd voordat je een keuze maakt. Aan de informatie in dit dashboard kunnen geen rechten worden ontleend.
  Zie je een fout of verouderde wachttijd? Gebruik de knop <b>Suggestie indienen</b> rechtsboven.
</p>

<script>
(function () {{
  var DATA = {data_json};
  var CAT_LABELS = {cat_labels_json};
  var MAPPED = {mapped_json};

  var state = {{ sortKey: "weken_sort", sortDir: "asc", search: "", categorie: "", level: "", status: "", locatie: "", wekenBracket: null }};

  var statusLabels = {{
    bekend: "Bekend", geen_wachtlijst: "Geen wachtlijst", aanmeldstop: "Aanmeldstop",
    geen_wachttijd_concept: "Geen wachttijd-concept", onbekend: "Onbekend"
  }};

  function fmtIntake(r) {{
    // Wachttijd (tot intake) en aanmeldwachttijd zijn hetzelfde gegeven --
    // 1 kolom. Toon de aanmeld_weken-waarde (kan een range zijn, bv. "2-8")
    // indien bekend, anders de algemene weken_sort/status-badge.
    if (r.status === "geen_wachttijd_concept") {{
      return statusLabels[r.status];
    }}
    if (r.aanmeld_weken) {{
      return r.aanmeld_weken + " weken" + (statusLabels[r.status] && r.status !== "bekend" ? " (" + statusLabels[r.status] + ")" : "");
    }}
    if (r.weken_sort === null || r.weken_sort === undefined) {{
      if (r.status === "bekend" && r.wachttijd) {{
        var short = r.wachttijd.replace(/\s+/g, " ").trim();
        return short.length > 45 ? short.substring(0, 43) + "\u2026" : short;
      }}
      return statusLabels[r.status] || "Onbekend";
    }}
    var wStr = String(r.weken_sort).replace(".", ",");
    return wStr + " weken" + (statusLabels[r.status] && r.status !== "bekend" ? " (" + statusLabels[r.status] + ")" : "");
  }}

  function fmtSplit(weeks, status) {{
    if (status === "geen_wachttijd_concept") return "\u2014";
    if (weeks === null || weeks === undefined || weeks === "") return "—";
    return weeks; // already formatted server-side: plain number ("35"), decimal
                  // ("4,5") or range ("2-8")
  }}

  function rankSplit(weeks, status) {{
    if (status === "geen_wachttijd_concept") return -1;
    if (weeks === null || weeks === undefined || weeks === "") return Infinity;
    var m = String(weeks).match(/[\\d.,]+/);
    return m ? parseFloat(m[0].replace(",", ".")) : Infinity;
  }}

  function buildSummary() {{
    var cards = [
      {{ lbl: "Geen wachttijd-concept", colorCls: "sc-groen",
        count: DATA.filter(function(r){{ return r.status === "geen_wachttijd_concept"; }}).length,
        statusVal: "geen_wachttijd_concept" }},
      {{ lbl: "Geen wachtlijst", colorCls: "sc-groen",
        count: DATA.filter(function(r){{ return r.status === "geen_wachtlijst"; }}).length,
        statusVal: "geen_wachtlijst" }},
      {{ lbl: "0\u20134 weken", colorCls: "sc-groen",
        count: DATA.filter(function(r){{ return r.status === "bekend" && r.weken_sort !== null && r.weken_sort !== undefined && r.weken_sort <= 4; }}).length,
        statusVal: null, bracketVal: "0-4" }},
      {{ lbl: "4\u201310 weken", colorCls: "sc-blauw",
        count: DATA.filter(function(r){{ return r.status === "bekend" && r.weken_sort !== null && r.weken_sort !== undefined && r.weken_sort > 4 && r.weken_sort <= 10; }}).length,
        statusVal: null, bracketVal: "4-10" }},
      {{ lbl: "10\u201320 weken", colorCls: "sc-oranje",
        count: DATA.filter(function(r){{ return r.status === "bekend" && r.weken_sort !== null && r.weken_sort !== undefined && r.weken_sort > 10 && r.weken_sort <= 20; }}).length,
        statusVal: null, bracketVal: "10-20" }},
      {{ lbl: "20+ weken", colorCls: "sc-oranje",
        count: DATA.filter(function(r){{ return r.status === "bekend" && r.weken_sort !== null && r.weken_sort !== undefined && r.weken_sort > 20; }}).length,
        statusVal: null, bracketVal: "20+" }},
      {{ lbl: "Aanmeldstop", colorCls: "sc-rood",
        count: DATA.filter(function(r){{ return r.status === "aanmeldstop"; }}).length,
        statusVal: "aanmeldstop" }},
      {{ lbl: "Onbekend", colorCls: "sc-grijs",
        count: DATA.filter(function(r){{ return r.status === "onbekend"; }}).length,
        statusVal: "onbekend" }},
    ];
    var container = document.getElementById("twd-summary");
    cards.forEach(function(c) {{
      var div = document.createElement("div");
      div.className = "twd-summary-card " + c.colorCls;
      if (c.statusVal || c.bracketVal) {{
        div.style.cursor = "pointer";
        div.onclick = function() {{
          var wasActive = div.classList.contains("active");
          container.querySelectorAll(".twd-summary-card.active").forEach(function(el) {{ el.classList.remove("active"); }});
          if (!wasActive) {{
            if (c.statusVal) {{
              document.getElementById("f-status").value = c.statusVal;
              state.status = c.statusVal;
              state.wekenBracket = null;
            }} else {{
              document.getElementById("f-status").value = "";
              state.status = "";
              state.wekenBracket = c.bracketVal;
            }}
            div.classList.add("active");
          }} else {{
            document.getElementById("f-status").value = "";
            state.status = "";
            state.wekenBracket = null;
          }}
          render();
        }};
      }}
      div.innerHTML = '<div class="sc-num">' + c.count + '</div><div class="sc-lbl">' + c.lbl + '</div>';
      container.appendChild(div);
    }});
  }}

    function populateLocaties() {{
    var sel = document.getElementById("f-locatie");
    var locs = Array.from(new Set(DATA.map(function (r) {{ return r.locatie; }}))).sort();
    locs.forEach(function (l) {{
      var o = document.createElement("option"); o.value = l; o.textContent = l; sel.appendChild(o);
    }});
  }}

  function applyFiltersAndSort() {{
    var rows = DATA.filter(function (r) {{
      if (state.categorie && r.categorieen.indexOf(state.categorie) === -1) return false;
      if (state.level && String(r.level) !== state.level) return false;
      if (state.status && r.status !== state.status) return false;
      if (state.wekenBracket) {{
        if (r.status !== "bekend") return false;
        var ws = r.weken_sort;
        if (ws === null || ws === undefined) return false;
        if (state.wekenBracket === "0-4"   && ws > 4)           return false;
        if (state.wekenBracket === "4-10"  && !(ws > 4 && ws <= 10))  return false;
        if (state.wekenBracket === "10-20" && !(ws > 10 && ws <= 20)) return false;
        if (state.wekenBracket === "20+"   && ws <= 20)          return false;
      }}
      if (state.locatie && r.locatie !== state.locatie) return false;
      if (state.search) {{
        var s = state.search.toLowerCase();
        var hay = (r.naam + " " + r.locatie + " " + r.website + " " + (r.email || "")).toLowerCase();
        if (hay.indexOf(s) === -1) return false;
      }}
      return true;
    }});

    rows.sort(function (a, b) {{
      if (state.sortKey === "weken_sort") {{
        function rank(r) {{
          if (r.status === "geen_wachttijd_concept") return -1;
          if (r.aanmeld_weken) {{
            var m2 = String(r.aanmeld_weken).match(/[\\d.,]+/);
            return m2 ? parseFloat(m2[0].replace(",", ".")) : Infinity;
          }}
          if (r.weken_sort === null || r.weken_sort === undefined || r.weken_sort === "") return Infinity;
          return r.weken_sort;
        }}
        var ra = rank(a), rb = rank(b);
        if (ra < rb) return state.sortDir === "asc" ? -1 : 1;
        if (ra > rb) return state.sortDir === "asc" ? 1 : -1;
        return 0;
      }}
      if (state.sortKey === "behandel_weken") {{
        var rsa = rankSplit(a[state.sortKey], a.status), rsb = rankSplit(b[state.sortKey], b.status);
        if (rsa < rsb) return state.sortDir === "asc" ? -1 : 1;
        if (rsa > rsb) return state.sortDir === "asc" ? 1 : -1;
        return 0;
      }}
      var ka = a[state.sortKey], kb = b[state.sortKey];
      var aNull = ka === null || ka === undefined || ka === "";
      var bNull = kb === null || kb === undefined || kb === "";
      if (aNull && bNull) return 0;
      if (aNull) return 1;
      if (bNull) return -1;
      if (typeof ka === "string") ka = ka.toLowerCase();
      if (typeof kb === "string") kb = kb.toLowerCase();
      if (ka < kb) return state.sortDir === "asc" ? -1 : 1;
      if (ka > kb) return state.sortDir === "asc" ? 1 : -1;
      return 0;
    }});
    return rows;
  }}

  function render() {{
    var rows = applyFiltersAndSort();
    var tbody = document.getElementById("twd-tbody");
    tbody.innerHTML = "";
    rows.forEach(function (r) {{
      var tr = document.createElement("tr");

      var tdNaam = document.createElement("td");
      var aNaam = document.createElement("a");
      var hrefNaam = r.website.indexOf("http") === 0 ? r.website : "https://" + r.website;
      aNaam.href = hrefNaam; aNaam.textContent = r.naam; aNaam.target = "_blank"; aNaam.rel = "noopener noreferrer"; aNaam.className = "twd-website";
      tdNaam.appendChild(aNaam);
      tr.appendChild(tdNaam);

      var tdLevel = document.createElement("td");
      var badgeLvl = document.createElement("span");
      badgeLvl.textContent = r.zorgintensiteit;
      tdLevel.appendChild(badgeLvl);
      tr.appendChild(tdLevel);

      var tdWt = document.createElement("td");
      var wtCell = document.createElement("div");
      wtCell.className = "twd-wt-cell";

      var span = document.createElement("span");
      var intakeBadge = r.status;
      if (r.status === "bekend") {{
        var sortVal = r.aanmeld_weken
          ? parseFloat(String(r.aanmeld_weken).match(/[\d.,]+/)[0].replace(",","."))
          : r.weken_sort;
        if (sortVal !== null && sortVal !== undefined && sortVal >= 10) intakeBadge = "laat";
      }}
      span.className = "twd-badge badge-" + intakeBadge;
      span.textContent = fmtIntake(r);
      if (r.wachttijd) span.setAttribute("data-tip", r.wachttijd);
      wtCell.appendChild(span);

      if (r.bron) {{
        var bronLink = document.createElement("a");
        bronLink.href = r.bron; bronLink.target = "_blank"; bronLink.rel = "noopener noreferrer";
        bronLink.textContent = "\u2197"; bronLink.className = "twd-link"; bronLink.title = "Bron bekijken";
        wtCell.appendChild(bronLink);
      }}
      tdWt.appendChild(wtCell);
      tr.appendChild(tdWt);

      var tdBehandel = document.createElement("td");
      var behandelVal = fmtSplit(r.behandel_weken, r.status);
      if (behandelVal && behandelVal !== "\u2014" && behandelVal !== "n.v.t.") {{
        var badgeB = document.createElement("span");
        badgeB.className = "twd-badge badge-bekend";
        badgeB.textContent = behandelVal + " weken";
        tdBehandel.appendChild(badgeB);
      }} else {{
        tdBehandel.textContent = behandelVal;
      }}
      tr.appendChild(tdBehandel);

      var tdTel = document.createElement("td"); tdTel.textContent = r.telefoon || "\u2014"; tr.appendChild(tdTel);

      var tdEmail = document.createElement("td");
      if (r.email && r.email !== "Onbekend") {{
        var aEmail = document.createElement("a");
        aEmail.href = "mailto:" + r.email; aEmail.textContent = r.email;
        aEmail.style.color = "#2E5C8A"; aEmail.style.fontSize = "12px"; aEmail.style.wordBreak = "break-all";
        tdEmail.appendChild(aEmail);
      }} else {{ tdEmail.textContent = "\u2014"; }}
      tr.appendChild(tdEmail);

      var tdLoc = document.createElement("td"); tdLoc.textContent = r.locatie; tr.appendChild(tdLoc);

      var tdCat = document.createElement("td");
      r.categorieen.forEach(function (c) {{
        var chip = document.createElement("span");
        chip.className = "twd-cat-chip";
        chip.textContent = CAT_LABELS[c] || c;
        tdCat.appendChild(chip);
      }});
      tr.appendChild(tdCat);

      tbody.appendChild(tr);
    }});

    document.getElementById("twd-count").textContent = rows.length + " van " + DATA.length + " praktijken";

    document.querySelectorAll(".twd-table th").forEach(function (th) {{
      var arrow = th.querySelector(".arrow");
      if (th.getAttribute("data-key") === state.sortKey) {{
        arrow.textContent = state.sortDir === "asc" ? "▲" : "▼";
      }} else {{
        arrow.textContent = "";
      }}
    }});
  }}

  document.querySelectorAll(".twd-table th").forEach(function (th) {{
    th.addEventListener("click", function () {{
      var key = th.getAttribute("data-key");
      if (state.sortKey === key) {{
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      }} else {{
        state.sortKey = key; state.sortDir = "asc";
      }}
      render();
    }});
  }});

  document.getElementById("f-search").addEventListener("input", function (e) {{ state.search = e.target.value; render(); }});
  document.getElementById("f-categorie").addEventListener("change", function (e) {{ state.categorie = e.target.value; render(); }});
  document.getElementById("f-level").addEventListener("change", function (e) {{ state.level = e.target.value; render(); }});
  document.getElementById("f-status").addEventListener("change", function (e) {{ state.status = e.target.value; render(); }});
  document.getElementById("f-locatie").addEventListener("change", function (e) {{ state.locatie = e.target.value; render(); }});

  populateLocaties();
  buildSummary();
  render();
}})();

// ── Column resize ──────────────────────────────────────────────────────────
(function () {{
  var table = document.querySelector('.twd-table');
  if (!table) return;
  var handles = table.querySelectorAll('thead .resize-handle');
  handles.forEach(function (handle) {{
    handle.addEventListener('mousedown', function (e) {{
      var th = handle.parentElement;
      var startX = e.pageX;
      var startW = th.offsetWidth;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      function onMove(e) {{
        var w = Math.max(40, startW + e.pageX - startX);
        th.style.width = w + 'px';
        th.style.minWidth = w + 'px';
      }}
      function onUp() {{
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        handle.classList.remove('resizing');
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }}
      handle.classList.add('resizing');
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
      e.preventDefault();
    }});
  }});
}})();


function submitSuggestie() {{
  var naam    = document.getElementById('sug-naam').value.trim();
  var praktijk = document.getElementById('sug-praktijk').value.trim();
  var tekst   = document.getElementById('sug-tekst').value.trim();
  var link    = document.getElementById('sug-link').value.trim();
  if (!praktijk || !tekst) {{
    alert('Vul minimaal de praktijknaam en een toelichting in.');
    return;
  }}
  var btn = document.querySelector('.twd-modal-submit');
  btn.disabled = true; btn.textContent = 'Versturen...';
  fetch('https://script.google.com/macros/s/AKfycbyNCyAS4fb_IZ8NsLWvgaNEvZrfQGpbNeS3cFyBMGbIUAMsREglAPP5ZtVu3bGMhm-8/exec', {{
    method: 'POST',
    mode: 'no-cors',
    body: JSON.stringify({{ naam: naam, praktijk: praktijk, opmerking: tekst, link: link }})
  }})
  .then(function() {{
    btn.disabled = false; btn.textContent = 'Versturen';
    document.getElementById('twd-suggest-overlay').classList.remove('open');
    document.getElementById('sug-naam').value = '';
    document.getElementById('sug-praktijk').value = '';
    document.getElementById('sug-tekst').value = '';
    document.getElementById('sug-link').value = '';
    alert('Bedankt! Je suggestie is ontvangen en wordt zo snel mogelijk nagelopen.');
  }})
  .catch(function() {{
    btn.disabled = false; btn.textContent = 'Versturen';
    alert('Er ging iets mis. Probeer het later opnieuw.');
  }});
}}
</script>
</div>
</body>
</html>
""".format(data_json=data_json, cat_labels_json=cat_labels_json, mapped_json=mapped_json, cat_options_html=cat_options_html, n_total=n_total)

with open("dashboard_v3.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("rows:", len(DATA))
print("written dashboard_v3.html, bytes:", len(HTML.encode()))
