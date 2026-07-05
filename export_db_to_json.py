"""
export_db_to_json.py
Exporteer de actieve wachttijden uit wachttijden.db naar dashboard_data_v3.json.
Gebruik: python3 export_db_to_json.py [--db PATH] [--out PATH]
"""
import sqlite3, json, argparse, sys
from pathlib import Path

DEFAULT_DB  = Path(__file__).parent / 'wachttijden.db'
DEFAULT_OUT = Path(__file__).parent / 'dashboard_data_v3.json'

def export(db_path, out_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Haal alle praktijken op
    cur.execute("SELECT * FROM praktijken ORDER BY id")
    praktijken = {r['id']: dict(r) for r in cur.fetchall()}

    # Voeg locatie toe (primaire)
    cur.execute("SELECT praktijk_id, stad FROM locaties WHERE primair=1")
    for row in cur.fetchall():
        pid = row['praktijk_id']
        if pid in praktijken:
            praktijken[pid]['locatie'] = row['stad']

    # Voeg categorieën toe
    cur.execute("SELECT praktijk_id, GROUP_CONCAT(categorie) AS cats FROM praktijk_categorieen GROUP BY praktijk_id")
    for row in cur.fetchall():
        pid = row['praktijk_id']
        if pid in praktijken:
            cats = row['cats'].split(',') if row['cats'] else []
            praktijken[pid]['cats'] = cats
            praktijken[pid]['categorieen'] = str(cats)  # legacy formaat voor dashboard

    # Haal actieve wachttijden op (algemeen: zonder verzekeraar/behandeltype)
    cur.execute("""
        SELECT w.*, l.stad AS locatie_stad
        FROM wachttijden w
        LEFT JOIN locaties l ON l.id = w.locatie_id
        WHERE w.actief = 1
          AND w.verzekeraar IS NULL
          AND w.behandeltype IS NULL
        ORDER BY w.praktijk_id
    """)
    wachttijden = {}
    for row in cur.fetchall():
        pid = row['praktijk_id']
        wachttijden[pid] = dict(row)

    con.close()

    result = []
    for pid, p in praktijken.items():
        w = wachttijden.get(pid, {})

        # weken_sort voor sortering (laagste aanmeld-grens)
        a_min = w.get('aanmeld_weken_min')
        weken_sort = a_min if a_min is not None else None

        # aanmeld_weken als string (bv. "8" of "4-12")
        a_lo = w.get('aanmeld_weken_min')
        a_hi = w.get('aanmeld_weken_max')
        if a_lo is not None:
            aanmeld_weken = str(a_lo) if a_lo == a_hi else f"{a_lo}-{a_hi}"
        else:
            aanmeld_weken = None

        # behandel_weken als string
        b_lo = w.get('behandel_weken_min')
        b_hi = w.get('behandel_weken_max')
        if b_lo is not None:
            behandel_weken = str(b_lo) if b_lo == b_hi else f"{b_lo}-{b_hi}"
        else:
            behandel_weken = None

        rec = {
            'row_id':        p.get('row_id'),
            'naam':          p.get('naam'),
            'website':       p.get('website'),
            'telefoon':      p.get('telefoon'),
            'email':         p.get('email'),
            'level':         p.get('level'),
            'locatie':       p.get('locatie', ''),
            'locatie_norm':  p.get('locatie', ''),
            'categorieen':   p.get('categorieen', '[]'),
            'cats':          p.get('cats', []),
            'status':        w.get('status', 'onbekend'),
            'weken_sort':    weken_sort,
            'aanmeld_weken': aanmeld_weken,
            'behandel_weken':behandel_weken,
            'wachttijd':     w.get('toelichting'),
            'bron':          w.get('bron_url'),
        }
        result.append(rec)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Geëxporteerd: {len(result)} praktijken → {out_path}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Exporteer wachttijden.db naar JSON')
    ap.add_argument('--db',  default=str(DEFAULT_DB),  help='Pad naar de SQLite database')
    ap.add_argument('--out', default=str(DEFAULT_OUT), help='Uitvoerpad voor de JSON')
    args = ap.parse_args()
    export(args.db, args.out)
