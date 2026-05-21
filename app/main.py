"""FastAPI Web-UI fuer AWeber-Operationen.

Mobile-tauglich. Dieselbe Logik wie aweber_cli.py auf dem Server.
BasicAuth via env vars BASIC_AUTH_USER + BASIC_AUTH_PASS.

Doktrin: msc-verfassung/marketing-doktrin/02-tagging-doktrin.md
"""
import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import gate

app = FastAPI(title="MSC AWeber Tool", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

security = HTTPBasic()
BASIC_AUTH_USER = os.environ.get("BASIC_AUTH_USER", "ar")
BASIC_AUTH_PASS = os.environ.get("BASIC_AUTH_PASS", "")


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if not BASIC_AUTH_PASS:
        raise HTTPException(status_code=503, detail="BASIC_AUTH_PASS not configured")
    ok_u = secrets.compare_digest(credentials.username, BASIC_AUTH_USER)
    ok_p = secrets.compare_digest(credentials.password, BASIC_AUTH_PASS)
    if not (ok_u and ok_p):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth required",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(require_auth)):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "lifecycle": gate.get_lifecycle_distribution(),
            "engagement": gate.get_engagement_distribution(),
            "verbundenheit": gate.get_verbundenheit_distribution(),
            "aktionen": gate.list_active_actions(),
        },
    )


@app.get("/journey", response_class=HTMLResponse)
def journey_form(request: Request, email: str | None = None, user: str = Depends(require_auth)):
    data = gate.get_customer_journey(email) if email else None
    return templates.TemplateResponse(
        "journey.html",
        {"request": request, "email": email or "", "data": data},
    )


@app.get("/kohorte", response_class=HTMLResponse)
def kohorte_form(request: Request, grp: str | None = None, user: str = Depends(require_auth)):
    members = gate.list_kohorte_members(grp) if grp else None
    return templates.TemplateResponse(
        "kohorte.html",
        {"request": request, "grp": grp or "", "members": members,
         "aktionen": gate.list_active_actions()},
    )


@app.get("/status", response_class=HTMLResponse)
def status_form(request: Request, eng: str | None = None, user: str = Depends(require_auth)):
    members = gate.list_status_members(eng) if eng else None
    return templates.TemplateResponse(
        "status.html",
        {"request": request, "eng": eng or "", "members": members,
         "eng_tags": gate.ENG_TAGS},
    )


@app.get("/aktion", response_class=HTMLResponse)
def aktion_form(request: Request, grp: str | None = None, user: str = Depends(require_auth)):
    data = gate.get_action_state(grp) if grp and grp.startswith("grp-") else None
    return templates.TemplateResponse(
        "aktion.html",
        {"request": request, "grp": grp or "", "data": data,
         "aktionen": gate.list_active_actions()},
    )


@app.get("/tag", response_class=HTMLResponse)
def tag_form(request: Request, user: str = Depends(require_auth)):
    return templates.TemplateResponse("tag.html", {"request": request, "result": None})


@app.post("/tag", response_class=HTMLResponse)
def tag_apply(
    request: Request,
    email: str = Form(...),
    add_tags: str = Form(""),
    remove_tags: str = Form(""),
    user: str = Depends(require_auth),
):
    add = [t.strip() for t in add_tags.split(",") if t.strip()]
    remove = [t.strip() for t in remove_tags.split(",") if t.strip()]
    try:
        result = gate.bulk_tags(email, add, remove)
        error = None
    except Exception as e:
        result, error = None, str(e)
    return templates.TemplateResponse(
        "tag.html",
        {"request": request, "result": result, "error": error,
         "email_val": email, "add_val": add_tags, "remove_val": remove_tags},
    )


@app.get("/aktion-lifecycle", response_class=HTMLResponse)
def aktion_lifecycle_form(request: Request, user: str = Depends(require_auth)):
    return templates.TemplateResponse(
        "aktion_lifecycle.html",
        {"request": request, "result": None, "phases": gate.PHASES, "stages": gate.FUNNEL_STAGES,
         "aktionen": gate.list_active_actions()},
    )


@app.post("/aktion-lifecycle/prepare", response_class=HTMLResponse)
def lifecycle_prepare(
    request: Request,
    grp: str = Form(...),
    include: str = Form(""),
    exclude: str = Form(""),
    dry_run: bool = Form(True),
    user: str = Depends(require_auth),
):
    body = {
        "target_include": [t.strip() for t in include.split(",") if t.strip()],
        "target_exclude": [t.strip() for t in exclude.split(",") if t.strip()],
        "start_phase": "phase-preprel",
        "start_stufe": "act-noeng",
        "dry_run": dry_run,
    }
    try:
        result = gate.action_prepare(grp, body)
        error = None
    except Exception as e:
        result, error = None, str(e)
    return templates.TemplateResponse(
        "aktion_lifecycle.html",
        {"request": request, "result": result, "error": error, "action": "prepare",
         "phases": gate.PHASES, "stages": gate.FUNNEL_STAGES,
         "aktionen": gate.list_active_actions()},
    )


@app.post("/aktion-lifecycle/transition", response_class=HTMLResponse)
def lifecycle_transition(
    request: Request,
    grp: str = Form(...),
    from_phase: str = Form(...),
    to_phase: str = Form(...),
    min_stufe: str = Form("act-open"),
    dropout: str = Form("keep_phase"),
    dry_run: bool = Form(True),
    user: str = Depends(require_auth),
):
    body = {
        "from_phase": from_phase, "to_phase": to_phase, "min_stufe": min_stufe,
        "on_dropout": dropout, "reset_stufe": "act-noeng", "dry_run": dry_run,
    }
    try:
        result = gate.action_phase_transition(grp, body)
        error = None
    except Exception as e:
        result, error = None, str(e)
    return templates.TemplateResponse(
        "aktion_lifecycle.html",
        {"request": request, "result": result, "error": error, "action": "transition",
         "phases": gate.PHASES, "stages": gate.FUNNEL_STAGES,
         "aktionen": gate.list_active_actions()},
    )


@app.post("/aktion-lifecycle/cleanup", response_class=HTMLResponse)
def lifecycle_cleanup(
    request: Request,
    grp: str = Form(...),
    dry_run: bool = Form(True),
    user: str = Depends(require_auth),
):
    try:
        result = gate.action_cleanup(grp, {"dry_run": dry_run})
        error = None
    except Exception as e:
        result, error = None, str(e)
    return templates.TemplateResponse(
        "aktion_lifecycle.html",
        {"request": request, "result": result, "error": error, "action": "cleanup",
         "phases": gate.PHASES, "stages": gate.FUNNEL_STAGES,
         "aktionen": gate.list_active_actions()},
    )
