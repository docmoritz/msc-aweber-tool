# msc-aweber-tool

Mobile-fähige Web-UI für AWeber-Operationen gemäß Tagging-Doktrin v2.

**Live:** https://aweber-tool.docmoritz.academy (BasicAuth, AR-only)
**Doktrin:** [msc-verfassung/marketing-doktrin/02-tagging-doktrin.md](https://github.com/docmoritz/msc-verfassung/blob/master/marketing-doktrin/02-tagging-doktrin.md)

## Was kannst du damit

| Seite | Funktion |
|---|---|
| `/` | Übersicht — Lifecycle, Engagement (Funnel-Bild), Verbundenheit, Aktive Aktionen |
| `/journey?email=X` | Customer Journey strukturiert nach Ebenen |
| `/kohorte?grp=grp-...` | Mitglieder einer Gruppe mit Engagement-Status |
| `/status?eng=eng-hot` | Wer ist in diesem Engagement-Status? |
| `/aktion?grp=grp-...` | Phase × Stufe Matrix einer laufenden Aktion |
| `/tag` | Tags atomar setzen / entfernen |
| `/aktion-lifecycle` | Aktion vorbereiten / Phase wechseln / abschließen |

Alle Schreib-Operationen unterstützen **Dry-Run** als Default.

## Architektur

```
Browser → FastAPI (BasicAuth) → aweber-gate (Bearer) → AWeber Public API
```

Gleiche Logik wie das CLI `/opt/msc/scripts/marketing/aweber_cli.py` und der Claude-Skill `/aweber`. Drei Wege auf dieselbe Funktionalität.

## Local Development

```bash
cp .env.example .env
# .env mit echtem AWEBER_GATE_API_KEY + BASIC_AUTH_PASS füllen

pip install -r requirements.txt
uvicorn app.main:app --reload
# http://127.0.0.1:8000 → BasicAuth-Prompt
```

## Deployment via Coolify

**Voraussetzungen:**
1. DNS A-Record `aweber-tool.docmoritz.academy` → Hetzner-IP (89.167.114.245)
2. Coolify hat Zugang zum Repo (GitHub App `microskills-github` ist Standard)

**Coolify-Setup:**
1. Neues Projekt → "Public Repository" → `https://github.com/docmoritz/msc-aweber-tool`
2. Branch: `main`
3. Build Pack: Dockerfile (auto-erkannt)
4. Domain: `aweber-tool.docmoritz.academy`
5. Environment Variables:
   - `AWEBER_GATE_API_KEY` = (aus `/etc/msc/aweber-gate.env`)
   - `BASIC_AUTH_PASS` = `<sicheres-passwort>` (notieren!)
   - `BASIC_AUTH_USER` = `ar` (optional, default)
6. Deploy → Coolify baut Container, holt Let's-Encrypt-Cert, route auf Subdomain
7. Auto-Deploy bei jedem `git push origin main` aktivieren

**Smoke-Test nach Deploy:**
```bash
curl -sk https://aweber-tool.docmoritz.academy/healthz
# {"status": "ok"}
```

## Sicherheit

- BasicAuth schützt alle Routen außer `/healthz`
- `BASIC_AUTH_PASS` als Coolify-Secret setzen (nicht im Repo)
- `AWEBER_GATE_API_KEY` ebenfalls als Secret
- AR-only Tool — kein Public Access

## Doktrin-Konformität

Alle Tag-Operationen gehen über `aweber-gate`, das die Doktrin (Präfix-Validation) erzwingt. Tags ohne `act-/phase-/eng-/lc-/vb-/grp-` werden vom Gate abgelehnt.

## Verwandt

- **CLI auf Server:** `/opt/msc/scripts/marketing/aweber_cli.py help`
- **Claude-Skill:** `/aweber help` (lokal, ruft Server-CLI via SSH)
- **AR-Skill:** `/controlling` (Daily-Multi-Source-Status)
