---
name: App (FastAPI)
typ: dienst
zweck: FastAPI-Anwendung mit BasicAuth, HTML-Templates und AWeber-Gate-Client fuer alle Web-UI-Routen
trigger: permanent
output: HTML-Responses ueber Jinja2-Templates; JSON via /healthz
abhaengigkeiten: aweber-gate (gate.py), FastAPI, Jinja2, httpx
wiki: true
---

# app

FastAPI-Applikation des MSC AWeber Tools.

## Technisches

**Entry-Point:**
```bash
uvicorn app.main:app --reload
```

**Wichtige Dateien:**
- `main.py` — FastAPI-App, Routen, BasicAuth-Middleware
- `gate.py` — HTTP-Client fuer aweber-gate (Bearer-Auth)
- `templates/` — Jinja2-HTML-Templates fuer alle Seiten
- `static/style.css` — CSS fuer mobile-taugliche Darstellung

**Routen (siehe main.py):**
- `GET /` — Uebersicht (Lifecycle, Engagement, Verbundenheit, Aktionen)
- `GET /journey` — Customer Journey nach Email
- `GET /kohorte` — Mitglieder einer Gruppe
- `GET /status` — Abonnenten nach Engagement-Status
- `GET /aktion` — Phase x Stufe Matrix
- `GET|POST /tag` — Tags atomar setzen/entfernen
- `GET|POST /aktion-lifecycle` — Aktion vorbereiten/Phase wechseln/abschliessen
- `GET /healthz` — Health-Check (kein Auth)

**Env-Vars:**
| Variable | Pflicht | Beschreibung |
|---|---|---|
| `BASIC_AUTH_PASS` | ja | Passwort fuer BasicAuth |
| `BASIC_AUTH_USER` | nein | Benutzername (default: `ar`) |
| `AWEBER_GATE_API_KEY` | ja | Bearer-Token fuer aweber-gate |
| `AWEBER_GATE_URL` | nein | Gate-URL (default: `https://aweber.docmoritz.academy`) |
| `AWEBER_LIST_ID` | nein | AWeber Listen-ID (default: `6953991`) |
