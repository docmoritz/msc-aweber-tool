---
name: MSC AWeber Tool – App
typ: dienst
zweck: FastAPI-Applikation mit Web-UI und AWeber-Gate-Client für Tag-Operationen
trigger: permanent
output: HTML-Seiten mit Lifecycle-, Engagement- und Tag-Ansichten
abhaengigkeiten: aweber-gate
wiki: true
---

# MSC AWeber Tool – App

FastAPI-Anwendung (Python) mit BasicAuth, Jinja2-Templates und einem HTTP-Client gegen `aweber-gate`.

## Technisches

**Entry-Point:** `app/main.py` (`uvicorn app.main:app`)
**Starten:** `uvicorn app.main:app --reload`
**Env-Vars:**
- `AWEBER_GATE_API_KEY` – Bearer-Token für aweber-gate (Pflicht)
- `BASIC_AUTH_PASS` – Passwort für BasicAuth (Pflicht)
- `AWEBER_GATE_URL` – Gate-URL (default: `https://aweber.docmoritz.academy`)
- `BASIC_AUTH_USER` – Benutzername für BasicAuth (default: `ar`)
- `AWEBER_LIST_ID` – AWeber-Listen-ID (default: `6953991`)

## Inhalt

| Datei | Zweck |
|-------|-------|
| `main.py` | FastAPI-Routen, BasicAuth, Template-Rendering |
| `gate.py` | HTTP-Client gegen aweber-gate (Tag-Operationen, Abfragen) |
| `templates/` | Jinja2-HTML-Templates für alle Seiten |
| `static/` | CSS-Stylesheet (`style.css`) |
