"""Client fuer aweber-gate (https://aweber.docmoritz.academy)."""
# Windows-Workaround: truststore VOR httpx importieren damit System-CA-Bundle
# benutzt wird (sonst SSL_CERTIFICATE_VERIFY_FAILED bei lokalem Test).
# In Linux-Containern (Coolify) ueberfluessig aber harmlos.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import os
from collections import Counter
from typing import Any

import httpx

GATE_URL = os.environ.get("AWEBER_GATE_URL", "https://aweber.docmoritz.academy")
GATE_TOKEN = os.environ.get("AWEBER_GATE_API_KEY", "")
# Welt-Listen-Identity: MSC-Tool bedient die Microskills-Liste explizit (Gate-Default
# wird abgeschafft). Env-ueberschreibbar.
LIST_ID = os.environ.get("AWEBER_LIST_ID", "6953991")
TIMEOUT = 20


def _u(path: str) -> str:
    """Gate-URL inkl. expliziter list_id (welt-eigene Listen-Identity)."""
    sep = "&" if "?" in path else "?"
    return f"{GATE_URL}{path}{sep}list_id={LIST_ID}"

FUNNEL_STAGES = ("noeng", "open", "intent", "hot", "conv")
PHASES = ("preprel", "prel", "cart", "post")
ENG_TAGS = [f"eng-{s}" for s in FUNNEL_STAGES] + ["eng-stale"]
LC_TAGS = ["lc-prospect", "lc-lead", "lc-paid"]


def _headers():
    return {"Authorization": f"Bearer {GATE_TOKEN}", "Content-Type": "application/json"}


def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT, headers=_headers(), verify=True)


def get_subscribers() -> list[dict]:
    with _client() as c:
        r = c.get(_u("/subscribers"))
        r.raise_for_status()
        d = r.json()
        return d.get("subscribers") or d.get("entries") or []


def get_action_state(grp_tag: str) -> dict:
    with _client() as c:
        r = c.get(f"{GATE_URL}/actions/{grp_tag}/state")
        r.raise_for_status()
        return r.json()


def get_broadcast_stats(broadcast_id: int) -> dict:
    """Broadcast-Stats vom Gate abrufen und auf kanonische Felder normalisieren.

    Das Gate liefert: total_sent / total_unique_opens / total_clicks.
    Aeltere Gate-Versionen nutzen: num_sent / unique_opens / unique_clicks.
    Beide werden unterstuetzt; die neuen Felder haben Vorrang.

    Rueckgabe-Felder:
        sends       -- Anzahl gesendeter Mails
        opens       -- Eindeutige Oeffnungen
        clicks      -- Eindeutige Klicks
        open_rate   -- Oeffnungsrate (0.0-1.0)
        click_rate  -- Klickrate (0.0-1.0)
        subject     -- Betreff der Broadcast-Mail (falls vom Gate geliefert)
        sent_at     -- ISO-8601-Zeitstempel des Versandzeitpunkts (falls vorhanden)
        broadcast_id -- Echo der abgefragten ID
    """
    with _client() as c:
        r = c.get(_u(f"/broadcasts/{broadcast_id}/stats"))
        if r.status_code == 404:
            return {"_hinweis": "broadcast_not_found", "broadcast_id": broadcast_id}
        r.raise_for_status()
        raw = r.json()

    # Feld-Normalisierung: neue Namen bevorzugen, alte als Fallback
    sends = raw.get("total_sent") if raw.get("total_sent") is not None else raw.get("num_sent")
    opens = raw.get("total_unique_opens") if raw.get("total_unique_opens") is not None else raw.get("unique_opens")
    clicks = raw.get("total_clicks") if raw.get("total_clicks") is not None else raw.get("unique_clicks")

    return {
        "broadcast_id": broadcast_id,
        "sends": sends,
        "opens": opens,
        "clicks": clicks,
        "open_rate": raw.get("open_rate"),
        "click_rate": raw.get("click_rate"),
        "subject": raw.get("subject"),
        "sent_at": raw.get("sent_at"),
    }


def list_broadcasts(status_filter: str = "sent", limit: int = 10, list_id: str | None = None) -> list[dict]:
    """Broadcasts vom Gate abrufen (neueste zuerst).

    Args:
        status_filter: Gate-Query-Param (NICHT 'status' — FastAPI ignoriert unbekannte
                       Params still). Erlaubte Werte: 'sent', 'scheduled', 'draft'.
        limit:         Maximale Anzahl zurueckgegebener Broadcasts.
        list_id:       AWeber-Listen-ID; wird aus Env uebernommen, wenn None.

    Rueckgabe: Liste von Dicts mit id, subject, sent_at, status.
    """
    lid = list_id or LIST_ID
    params = f"status_filter={status_filter}&limit={limit}&list_id={lid}"
    url = f"{GATE_URL}/broadcasts?{params}"
    with _client() as c:
        r = c.get(url)
        r.raise_for_status()
        data = r.json()
    # Gate kann Liste direkt oder unter 'broadcasts'-Schluessel liefern
    entries = data if isinstance(data, list) else data.get("broadcasts") or data.get("entries") or []
    return [
        {
            "id": e.get("id"),
            "subject": e.get("subject"),
            "sent_at": e.get("sent_at"),
            "status": e.get("status"),
        }
        for e in entries
    ]


def get_latest_broadcast(list_id: str | None = None) -> dict | None:
    """Convenience: letzten gesendeten Broadcast mit Stats zurueckgeben oder None."""
    broadcasts = list_broadcasts(status_filter="sent", limit=1, list_id=list_id)
    if not broadcasts:
        return None
    bid = broadcasts[0].get("id")
    if not bid:
        return None
    stats = get_broadcast_stats(bid)
    return {**broadcasts[0], **stats}


def bulk_tags(email: str, add: list[str], remove: list[str]) -> dict:
    with _client() as c:
        r = c.post(
            _u(f"/subscribers/{email}/tags/bulk"),
            json={"add": add, "remove": remove},
        )
        r.raise_for_status()
        return r.json()


def set_custom_fields(email: str, fields: dict) -> dict:
    with _client() as c:
        r = c.post(_u(f"/subscribers/{email}/custom-fields"), json=fields)
        r.raise_for_status()
        return r.json()


def action_prepare(grp_tag: str, body: dict) -> dict:
    with _client() as c:
        r = c.post(f"{GATE_URL}/actions/{grp_tag}/prepare", json=body)
        r.raise_for_status()
        return r.json()


def action_phase_transition(grp_tag: str, body: dict) -> dict:
    with _client() as c:
        r = c.post(f"{GATE_URL}/actions/{grp_tag}/phase-transition", json=body)
        r.raise_for_status()
        return r.json()


def action_cleanup(grp_tag: str, body: dict) -> dict:
    with _client() as c:
        r = c.post(f"{GATE_URL}/actions/{grp_tag}/cleanup", json=body)
        r.raise_for_status()
        return r.json()


# ----- Aggregator (clientseitig aus Subscriber-Liste) ----------------------


def get_lifecycle_distribution() -> dict:
    subs = get_subscribers()
    result = {t: 0 for t in LC_TAGS}
    for e in subs:
        for t in e.get("tags", []) or []:
            if t in result:
                result[t] += 1
    result["total"] = len(subs)
    return result


def get_engagement_distribution() -> dict:
    subs = get_subscribers()
    result = {t: 0 for t in ENG_TAGS}
    without_eng = 0
    for e in subs:
        tags = e.get("tags", []) or []
        has_eng = False
        for t in tags:
            if t in result:
                result[t] += 1
                if t != "eng-stale":
                    has_eng = True
        if not has_eng:
            without_eng += 1
    result["total"] = len(subs)
    result["without_eng"] = without_eng
    return result


def get_verbundenheit_distribution() -> dict:
    subs = get_subscribers()
    counter: Counter = Counter()
    for e in subs:
        for t in e.get("tags", []) or []:
            if t.startswith("vb-"):
                counter[t] += 1
    return dict(counter)


def get_groups_distribution() -> dict:
    subs = get_subscribers()
    counter: Counter = Counter()
    for e in subs:
        for t in e.get("tags", []) or []:
            if t.startswith("grp-"):
                counter[t] += 1
    return dict(counter)


def list_active_actions() -> list[dict]:
    subs = get_subscribers()
    actions: dict[str, dict] = {}
    for e in subs:
        tags = e.get("tags", []) or []
        grp_tags = [t for t in tags if t.startswith("grp-")]
        has_phase = any(t.startswith("phase-") for t in tags)
        for g in grp_tags:
            a = actions.setdefault(g, {"action": g, "members": 0, "with_phase": 0})
            a["members"] += 1
            if has_phase:
                a["with_phase"] += 1
    return sorted(actions.values(), key=lambda a: (-a["with_phase"], -a["members"]))


def get_customer_journey(email: str) -> dict:
    subs = get_subscribers()
    hits = [e for e in subs if (e.get("email", "") or "").lower() == email.lower()]
    if not hits:
        return {"_hinweis": "not_found", "email": email}
    s = hits[0]
    tags = s.get("tags", []) or []
    phase = next((t for t in tags if t.startswith("phase-")), None)
    stufe = next((t for t in tags if t.startswith("act-")), None)
    gruppen = [t for t in tags if t.startswith("grp-")]
    aktion = {"grp": gruppen[0] if gruppen else None, "phase": phase, "stufe": stufe} if phase and stufe else None
    return {
        "email": s.get("email"),
        "lifecycle": next((t for t in tags if t in LC_TAGS), None),
        "engagement": next((t for t in tags if t.startswith("eng-") and t != "eng-stale"), None),
        "stale": "eng-stale" in tags,
        "verbundenheit": [t for t in tags if t.startswith("vb-")],
        "gruppen": gruppen,
        "aktuelle_aktion": aktion,
        "custom_fields": s.get("custom_fields") or {},
        "subscribed_at": str(s.get("subscribed_at") or ""),
        "alle_tags": sorted(tags),
    }


def list_kohorte_members(grp_tag: str) -> list[dict]:
    subs = get_subscribers()
    members = []
    for e in subs:
        tags = e.get("tags", []) or []
        if grp_tag not in tags:
            continue
        cf = e.get("custom_fields") or {}
        members.append({
            "email": e.get("email"),
            "lifecycle": next((t for t in tags if t in LC_TAGS), None),
            "engagement": next((t for t in tags if t.startswith("eng-") and t != "eng-stale"), None),
            "stale": "eng-stale" in tags,
            "verbundenheit": [t for t in tags if t.startswith("vb-")],
            "engagement_set_at": cf.get("engagement_set_at"),
        })
    return members


def list_status_members(eng_tag: str) -> list[dict]:
    subs = get_subscribers()
    members = []
    for e in subs:
        tags = e.get("tags", []) or []
        if eng_tag not in tags:
            continue
        members.append({
            "email": e.get("email"),
            "lifecycle": next((t for t in tags if t in LC_TAGS), None),
            "gruppen": [t for t in tags if t.startswith("grp-")],
            "verbundenheit": [t for t in tags if t.startswith("vb-")],
            "stale": "eng-stale" in tags,
        })
    return members


def find_subscriber(email: str) -> dict | None:
    subs = get_subscribers()
    hits = [e for e in subs if (e.get("email", "") or "").lower() == email.lower()]
    return hits[0] if hits else None
