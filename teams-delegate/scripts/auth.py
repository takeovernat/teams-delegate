#!/usr/bin/env python3
"""
teams-delegate auth — Microsoft Graph OAuth2 device code flow.
Usage: python3 auth.py [--client-id YOUR_CLIENT_ID]
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

TOKEN_DIR = os.path.expanduser("~/.teams-delegate")
TOKEN_FILE = os.path.join(TOKEN_DIR, "token.json")
CONFIG_FILE = os.path.join(TOKEN_DIR, "config.json")

SCOPES = [
    "Chat.Read",
    "Chat.ReadWrite",
    "ChannelMessage.Read.All",
    "ChannelMessage.Send",
    "Presence.Read.All",
    "User.Read",
    "offline_access",
]

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    os.makedirs(TOKEN_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def save_token(token_data):
    os.makedirs(TOKEN_DIR, exist_ok=True)
    token_data["saved_at"] = time.time()
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)


def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def is_token_valid(token_data):
    if not token_data:
        return False
    saved_at = token_data.get("saved_at", 0)
    expires_in = token_data.get("expires_in", 3600)
    return (time.time() - saved_at) < (expires_in - 60)


def refresh_token(token_data, client_id):
    refresh_tok = token_data.get("refresh_token")
    if not refresh_tok:
        return None
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok,
        "scope": " ".join(SCOPES),
    }).encode()
    req = urllib.request.Request(
        "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
        data=data,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            new_token = json.loads(resp.read())
            save_token(new_token)
            return new_token
    except Exception as e:
        print(f"Token refresh failed: {e}", file=sys.stderr)
        return None


def device_code_flow(client_id):
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "scope": " ".join(SCOPES),
    }).encode()
    req = urllib.request.Request(
        "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode",
        data=data,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            device = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\nDevice code request failed (HTTP {e.code}):", file=sys.stderr)
        print(body, file=sys.stderr)
        try:
            parsed = json.loads(body)
            print(f"\nError: {parsed.get('error')}", file=sys.stderr)
            print(f"Description: {parsed.get('error_description', '')}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)

    print(f"\n{device['message']}\n")

    poll_data = urllib.parse.urlencode({
        "client_id": client_id,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device["device_code"],
    }).encode()

    interval = device.get("interval", 5)
    expires = time.time() + device.get("expires_in", 900)

    while time.time() < expires:
        time.sleep(interval)
        req = urllib.request.Request(
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
            data=poll_data,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                token = json.loads(resp.read())
                save_token(token)
                print("Authentication complete.")
                return token
        except urllib.error.HTTPError as e:
            body = json.loads(e.read())
            err = body.get("error", "")
            if err == "authorization_pending":
                continue
            elif err == "slow_down":
                interval += 5
                continue
            else:
                print(f"Auth error: {err} — {body.get('error_description', '')}", file=sys.stderr)
                sys.exit(1)

    print("Authentication timed out.", file=sys.stderr)
    sys.exit(1)


def get_valid_token():
    config = load_config()
    client_id = config.get("client_id")
    if not client_id:
        print("No client_id configured. Run: python3 auth.py --client-id YOUR_CLIENT_ID", file=sys.stderr)
        sys.exit(1)

    token = load_token()
    if is_token_valid(token):
        return token["access_token"]

    if token and token.get("refresh_token"):
        refreshed = refresh_token(token, client_id)
        if refreshed:
            return refreshed["access_token"]

    token = device_code_flow(client_id)
    return token["access_token"]


def graph_get(path, access_token):
    req = urllib.request.Request(
        f"{GRAPH_BASE}{path}",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", help="Azure app client ID")
    args = parser.parse_args()

    if args.client_id:
        config = load_config()
        config["client_id"] = args.client_id
        save_config(config)
        print(f"Client ID saved.")

    token = get_valid_token()
    me = graph_get("/me", token)
    print(f"Authenticated as: {me.get('displayName')} ({me.get('mail') or me.get('userPrincipalName')})")
