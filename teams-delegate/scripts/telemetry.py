#!/usr/bin/env python3
"""
Anonymous usage telemetry for teams-delegate.
Sends a single ping to a free counter API on first run and version updates.
No personal data — just skill name, version, and a random install ID.
"""

import json, os, uuid, urllib.request, urllib.error, hashlib

TELEMETRY_FILE = os.path.expanduser("~/.teams-delegate/telemetry.json")
SKILL_VERSION  = "1.0.1"
# Free counter endpoint — replace with your own (plausible.io, umami, simple-analytics, or a Supabase edge function)
PING_URL = "https://api.countapi.xyz/hit/takeovernat/teams-delegate"

def get_install_id():
    """Generate a stable anonymous ID for this installation."""
    t = {}
    if os.path.exists(TELEMETRY_FILE):
        with open(TELEMETRY_FILE) as f:
            t = json.load(f)
    if "install_id" not in t:
        t["install_id"] = str(uuid.uuid4())
        os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)
        with open(TELEMETRY_FILE, "w") as f:
            json.dump(t, f)
    return t

def should_ping(t):
    return t.get("last_version") != SKILL_VERSION

def record_ping(t):
    t["last_version"] = SKILL_VERSION
    with open(TELEMETRY_FILE, "w") as f:
        json.dump(t, f)

def ping():
    try:
        t = get_install_id()
        if not should_ping(t):
            return
        req = urllib.request.Request(PING_URL, method="GET")
        req.add_header("User-Agent", f"teams-delegate/{SKILL_VERSION}")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            record_ping(t)
    except Exception:
        pass  # Never block on telemetry failure

if __name__ == "__main__":
    ping()
    print("Telemetry ping sent.")
