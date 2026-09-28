# bexio plugin

- `skills/` → 10 skills: `bexio` (core, load first) + 9 segments.
- `freigaben/freigaben.html` → Übersicht für Menschen: welche Aktion sofort läuft, welche ein Ja braucht, Ablauf als interaktives Diagramm, Warnungen, Skills. Im Browser öffnen.
- Neu erzeugen nach Änderung an Gate oder Texten: `python3 freigaben/gen.py` · Prüfen: `python3 freigaben/gen.py --check` (bricht ab, wenn die Freigabe-Liste nicht mit `skills/bexio/SKILL.md` §3.1 übereinstimmt).
