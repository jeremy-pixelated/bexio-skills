"""Build freigaben.html: Bexio write actions, gate, flow chart (German).
Inputs (this folder): write-actions.json (connector action list), texte_de.py (one German sentence per action), template.html.
Guard: gated set must equal core skill §3.1, every action needs a German text. Run: python3 gen.py [--check]"""
import json, html, re, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import texte_de
w = json.load(open(HERE / 'write-actions.json'))
core = (HERE.parent / 'skills' / 'bexio' / 'SKILL.md').read_text()
sec = core[core.index('### 3.1'):core.index('### 3.2')]
skill_gated = set(re.findall(r'^\| `(bexio_[a-z_]+\.[a-z_]+)` \|', sec, re.M))
data_gated = {f"{r['tool']}.{r['action']}" for r in w if r['gate'] == 'confirm'}
if skill_gated != data_gated or len(data_gated) != 46:
    sys.exit(f'gate drift: only skill {sorted(skill_gated - data_gated)} only data {sorted(data_gated - skill_gated)} n={len(data_gated)}')
missing = [(r['tool'], r['action']) for r in w if (r['tool'], r['action']) not in texte_de.DE]
if missing:
    sys.exit(f'no German text: {missing}')
skill = lambda g: 'bexio-admin' if g == 'misc' else 'bexio-' + g
ORDER = ['bexio-sales', 'bexio-purchase', 'bexio-banking', 'bexio-accounting', 'bexio-contacts', 'bexio-items', 'bexio-projects', 'bexio-files', 'bexio-admin']
rows = [dict(t=r['tool'], a=r['action'], s=skill(r['group']), g=int(r['gate'] == 'confirm'),
             c=r['cls'] if r['gate'] == 'confirm' else 'write', de=texte_de.DE[(r['tool'], r['action'])]) for r in w]
rows.append(dict(t='bexio_bills', a='create / update + payment', s='bexio-purchase', g=1, c='payment order',
                 de=texte_de.DE[('bexio_bills', 'create / update + payment')]))
rows.sort(key=lambda r: (-r['g'], ORDER.index(r['s']), r['t'], r['a']))
n_yes = len(data_gated)
n_dir = sum(1 for r in rows if not r['g'])
# Stand line: texte_de.STAND is a static string ("Stand <date> · v<n>"), bumped BY HAND on every text change
# (texte_de.py, template.html, FLAGS/SKILLS here). Never derive it at build time (git SHA, today's date):
# --check must stay idempotent, i.e. an unchanged source must regenerate byte-identical output.
FLAGS = [
 ('Periode abgeschlossen', 'closed_period', 'Das Buchungsdatum liegt in einem abgeschlossenen Geschäftsjahr.'),
 ('MWST schon abgerechnet', 'vat_period_filed', 'Das Datum liegt in einer MWST-Periode, die schon abgerechnet ist.'),
 ('Periode unklar', 'period_unknown', 'Datum fehlt oder passt zu keinem (oder mehreren) Geschäftsjahren bzw. MWST-Perioden.'),
 ('Doppelbuchung', 'duplicate', 'Es gibt schon eine gleiche manuelle Buchung (Datum, Konten, Betrag, Referenz).'),
 ('Über dem Limit', 'amount_over_limit', 'Der Betrag in CHF liegt über dem eingestellten Buchungslimit (nur wenn ein Limit gesetzt ist).'),
 ('Betrag unklar', 'amount_unknown', 'Betrag oder Währung lassen sich nicht bestimmen (nur wenn ein Limit gesetzt ist).'),
 ('Kein Wechselkurs', 'fx_rate_unknown', 'Bexio hat für dieses Datum keinen brauchbaren Kurs.'),
 ('Provisorischer Kurs', 'fx_rate_provisional', 'Bexio liefert nur einen Ersatzkurs. Er wird trotzdem verwendet.'),
 ('Kurs weicht ab', 'fx_rate_deviation', 'Der angegebene Kurs weicht mehr als 2 % vom Bexio-Kurs ab.'),
 ('Felder werden ignoriert', 'non_draft_fields_ignored', 'Änderung an einer schon gebuchten Lieferantenrechnung oder Spese: Bexio übernimmt nur einen Teil.'),
 ('Prüfung nicht möglich', 'check_unavailable', 'Eine Prüfung konnte ihre Daten nicht lesen. Wird nie als "in Ordnung" angenommen.'),
]
flag_codes = set(re.findall(r'`([a-z_]+)`', core[core.index('### 3.5'):core.index('## 4')])) if '### 3.5' in core else None
if flag_codes is not None and not {c for _, c, _ in FLAGS} <= flag_codes:
    sys.exit(f'flag drift vs core §3.5: {sorted({c for _, c, _ in FLAGS} - flag_codes)}')
SKILLS = [
 ('bexio', 'Kern · lädt immer zuerst', 'Freigabe-Regeln, Warnungen, Grundregeln der Schnittstelle, Fehler, was ohne Schnittstelle geht, Weiterleitung an die Bereiche.'),
 ('bexio-contacts', 'Kontakte', 'Kunden, Lieferanten, Personen, Verknüpfungen, Gruppen, Branchen, Zusatzadressen.'),
 ('bexio-sales', 'Verkauf', 'Offerten, Aufträge, Lieferscheine, Rechnungen, Positionen, Zahlungseingänge, Mahnungen.'),
 ('bexio-purchase', 'Einkauf', 'Lieferantenrechnungen, Spesen, Bestellungen, Zahlungen an Lieferanten.'),
 ('bexio-accounting', 'Buchhaltung', 'Manuelle Buchungen, Storno-Buchungen, Kontenplan, Geschäftsjahre, MWST-Perioden, Währungen, Journal.'),
 ('bexio-banking', 'Banking', 'Bankkonten, Zahlungsaufträge, offene und fehlgeschlagene Zahlungen, Bankabstimmung.'),
 ('bexio-items', 'Artikel', 'Artikelstamm, Preise, Steuer- und Konto-Vorgaben, Einheiten, Lagerorte.'),
 ('bexio-projects', 'Projekte', 'Projekte, Meilensteine, Arbeitspakete, Zeiterfassung, Tätigkeiten.'),
 ('bexio-files', 'Dateien', 'Bexio-Inbox: Belege hochladen, finden, umbenennen, archivieren, löschen.'),
 ('bexio-admin', 'Verwaltung', 'Benutzer und Rechte, fiktive Benutzer, Notizen, Aufgaben, Firmenprofil, Stammdaten.'),
]
e = html.escape
flags_html = ''.join(f'<tr><td><b>{e(n)}</b><br><code class="fc-code">{e(c)}</code></td><td>{e(d)}</td></tr>' for n, c, d in FLAGS)
skills_html = ''.join(f'<li class="sk"><div class="skn"><code>{e(n)}</code><span>{e(t)}</span></div><p>{e(d)}</p></li>' for n, t, d in SKILLS)
data = json.dumps(dict(rows=rows, cls=texte_de.CLS_DE), ensure_ascii=False)
body = ((HERE / 'template.html').read_text().replace('%%DATA%%', data).replace('%%FLAGS%%', flags_html)
        .replace('%%SKILLS%%', skills_html).replace('%%NYES%%', str(n_yes)).replace('%%NDIR%%', str(n_dir))
        .replace('%%NW%%', str(len(w))).replace('%%STAND%%', e(texte_de.STAND)))
cut = body.index('</style>') + len('</style>')
page = ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<style>html{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
        + body[:cut] + '\n</head>\n<body>\n' + body[cut:] + '\n</body>\n</html>\n')
out = HERE / 'freigaben.html'
if '--check' in sys.argv:
    sys.exit(0 if out.exists() and out.read_text() == page else 'freigaben.html is stale: run python3 gen.py')
out.write_text(page)
print(f'freigaben.html: {n_yes} gated, {n_dir} direct, {len(rows)} rows')
