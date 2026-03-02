# Teams Delegate — OpenClaw Skill

> Delegate your Microsoft Teams inbox to your AI agent. Auto-reply, summarize, and filter messages so you only see what actually needs your attention.

Built by **Nate Teshome** | [GitHub](https://github.com/takeovernat) | [stellarsitesai.com](https://stellarsitesai.com)

## Install

```bash
clawhub install teams-delegate
```

## What It Does

- Read your Teams inbox (1:1 chats, group chats, channels)
- Summarize unread conversations
- Auto-reply to low-stakes messages
- Escalate urgent messages from your boss
- Works fully from the terminal — no browser needed after setup

## Requirements

- Microsoft 365 license (work/school account or paid personal)
- Azure app registration (free) — see setup in SKILL.md
- OpenClaw + Python 3.9+

## Setup

```bash
# 1. Install
clawhub install teams-delegate

# 2. Register Azure app at portal.azure.com (see SKILL.md for full guide)
# 3. Auth
python3 scripts/auth.py --client-id YOUR_CLIENT_ID

# 4. Test
python3 scripts/teams.py inbox
```

## Usage

```bash
python3 scripts/teams.py inbox          # See recent chats
python3 scripts/teams.py summary        # AI-ready inbox dump
python3 scripts/teams.py read <chatId>  # Read a conversation
python3 scripts/teams.py reply <chatId> "your message"
```

## License

MIT — free to use and modify.

---

*Found a bug? Open an [issue](https://github.com/takeovernat/teams-delegate/issues). Want to contribute? PRs welcome.*
