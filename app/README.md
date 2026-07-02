---
name: MSC AWeber Tool — App-Paket
typ: dienst
zweck: FastAPI-Anwendungspaket mit Web-UI, Gate-Client und Jinja2-Templates für AWeber-Operationen.
trigger: permanent
output: HTML-Seiten (Jinja2), JSON-Antworten vom Gate
abhaengigkeiten: aweber-gate, fastapi, uvicorn, httpx, jinja2
wiki: true
---

# App-Paket

Enthält den gesamten Python-Quellcode der FastAPI-Anwendung.

## Technisches

**Entry-Point:**
```bash
uvicorn app.main:app --reload
```

**Dateien:**
- `main.py` — FastAPI-App, Routen, BasicAuth, Template-Rendering
- `gate.py` — HTTP-Client für aweber-gate; Aggregatoren (Lifecycle, Engagement, Verbundenheit)
- `templates/` — Jinja2-HTML-Templates je Route
- `static/` — CSS (style.css)

**Env-Vars (aus `.env.example`):**

| Variable | Pflicht | Default | Beschreibung |
|---|---|---|---|
| `AWEBER_GATE_API_KEY` | ja | — | Bearer-Token für aweber-gate |
| `BASIC_AUTH_PASS` | ja | — | Passwort für BasicAuth |
| `AWEBER_GATE_URL` | nein | `https://aweber.docmoritz.academy` | Gate-Basis-URL |
| `BASIC_AUTH_USER` | nein | `ar` | Benutzername für BasicAuth |
| `AWEBER_LIST_ID` | nein | `6953991` | AWeber-Listenkennung |
