#!/usr/bin/env python3
"""
teams-delegate core CLI — read, summarize, and reply to Microsoft Teams messages.

Usage:
  python3 teams.py inbox              # List unread/recent chats
  python3 teams.py read <chatId>      # Show messages in a chat
  python3 teams.py reply <chatId> "message"   # Send a reply
  python3 teams.py summary            # AI-ready summary of all pending messages
"""

import json
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from auth import get_valid_token, graph_get, GRAPH_BASE

GRAPH_BASE_URL = GRAPH_BASE


def strip_html(text):
    return re.sub(r"<[^<]+?>", "", text or "").strip()


def fmt_time(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%m/%d %I:%M %p")
    except Exception:
        return iso


def get_chats(token):
    data = graph_get(
        "/me/chats?$expand=lastMessagePreview&$orderby=lastMessagePreview/createdDateTime desc&$top=20",
        token
    )
    return data.get("value", [])


def get_messages(chat_id, token, top=10):
    data = graph_get(f"/me/chats/{chat_id}/messages?$top={top}", token)
    return data.get("value", [])


def send_reply(chat_id, message, token):
    url = f"{GRAPH_BASE_URL}/me/chats/{chat_id}/messages"
    body = json.dumps({
        "body": {"contentType": "text", "content": message}
    }).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def cmd_inbox(token):
    chats = get_chats(token)
    if not chats:
        print("No recent chats found.")
        return
    print(f"\n{'ID':<36}  {'Type':<10}  {'Last Message':<40}  {'Time'}")
    print("-" * 100)
    for chat in chats:
        chat_id = chat["id"]
        chat_type = chat.get("chatType", "unknown")
        preview = chat.get("lastMessagePreview", {})
        sender = preview.get("from", {}).get("user", {}).get("displayName", "Unknown")
        content = strip_html(preview.get("body", {}).get("content", ""))[:40]
        time_str = fmt_time(preview.get("createdDateTime", ""))
        print(f"{chat_id:<36}  {chat_type:<10}  {sender}: {content:<38}  {time_str}")


def cmd_read(chat_id, token):
    messages = get_messages(chat_id, token)
    messages.reverse()
    print(f"\nChat: {chat_id}\n" + "=" * 60)
    for msg in messages:
        sender = msg.get("from", {}).get("user", {}).get("displayName", "Unknown")
        content = strip_html(msg.get("body", {}).get("content", ""))
        time_str = fmt_time(msg.get("createdDateTime", ""))
        importance = msg.get("importance", "normal")
        flag = " [URGENT]" if importance == "urgent" else " [HIGH]" if importance == "high" else ""
        print(f"\n[{time_str}]{flag} {sender}:\n  {content}")


def cmd_summary(token):
    chats = get_chats(token)
    print("\n=== TEAMS INBOX SUMMARY ===\n")
    print("Use this to decide what needs a reply and draft responses.\n")
    for chat in chats[:10]:
        chat_id = chat["id"]
        chat_type = chat.get("chatType", "unknown")
        preview = chat.get("lastMessagePreview", {})
        sender = preview.get("from", {}).get("user", {}).get("displayName", "Unknown")
        content = strip_html(preview.get("body", {}).get("content", ""))
        time_str = fmt_time(preview.get("createdDateTime", ""))
        importance = preview.get("importance", "normal")
        print(f"CHAT_ID: {chat_id}")
        print(f"  Type: {chat_type} | From: {sender} | Time: {time_str} | Importance: {importance}")
        print(f"  Preview: {content[:120]}")
        print()


def cmd_reply(chat_id, message, token):
    result = send_reply(chat_id, message, token)
    print(f"Reply sent (id: {result.get('id', 'unknown')})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    token = get_valid_token()
    cmd = sys.argv[1]

    if cmd == "inbox":
        cmd_inbox(token)
    elif cmd == "read" and len(sys.argv) >= 3:
        cmd_read(sys.argv[2], token)
    elif cmd == "reply" and len(sys.argv) >= 4:
        cmd_reply(sys.argv[2], sys.argv[3], token)
    elif cmd == "summary":
        cmd_summary(token)
    else:
        print(__doc__)
        sys.exit(1)
