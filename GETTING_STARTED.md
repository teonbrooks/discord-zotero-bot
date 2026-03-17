# Getting Started with zotero-bot

This guide walks you through everything needed to get zotero-bot running in your Discord server from scratch.

---

## Prerequisites

- **Python 3.12 or later** — check with `python --version`
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager (`pip install uv` or see uv docs)
- A **Discord account** with permission to manage a server
- A **Zotero account** with a group library

---

## Step 1 — Create a Discord bot application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**
2. Give it a name (e.g. `zotero-bot`) and click **Create**
3. In the left sidebar, click **Bot**
4. Click **Reset Token**, confirm, and copy the token — you will need this for `DISCORD_TOKEN`
5. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent**
   - **Server Members Intent** (optional but recommended)
6. Click **Save Changes**

---

## Step 2 — Invite the bot to your server

1. Still in the Developer Portal, click **OAuth2** → **URL Generator** in the sidebar
2. Under **Scopes**, check:
   - `bot`
   - `applications.commands`
3. Under **Bot Permissions**, check:
   - Read Messages / View Channels
   - Read Message History
   - Add Reactions
4. Copy the generated URL, open it in your browser, and select the server you want to add the bot to
5. Click **Authorize**

---

## Step 3 — Set up your Zotero group library

1. Log in to [zotero.org](https://www.zotero.org) and create a group library if you do not already have one:
   - Click your username → **New Group**
   - Choose a name and set the group type (**Private**, **Public Closed**, or **Public Open**)
   - Note: Public Open groups cannot store files — the bot will attach linked URLs instead of PDFs
2. Find your **Group ID**: navigate to your group page; the ID is the number in the URL — `zotero.org/groups/{GROUP_ID}/`

### Create a Zotero API key

1. Go to [zotero.org/settings/keys](https://www.zotero.org/settings/keys) and click **Create new private key**
2. Give the key a description (e.g. `discord-zotero-bot`)
3. Under **Personal Library**, you can leave everything unchecked
4. Under **Default Group Permissions** or per-group permissions, enable:
   - **Read/Write** for your target group
5. Click **Save Key** and copy the key — you will need this for `ZOTERO_TOKEN`

---

## Step 4 — Install the bot

Clone or download the repository, then install dependencies:

```bash
cd zotero-bot
uv sync
```

---

## Step 5 — Configure environment variables

Copy the included example file and fill in your values:

```bash
cp .env.example .env
```

Then open `.env` and substitute your real credentials:

```env
# Discord bot token (from Step 1)
DISCORD_TOKEN=your_discord_token_here

# Zotero API key (from Step 3)
ZOTERO_TOKEN=your_zotero_api_key_here

# Zotero group ID (from Step 3)
ZOTERO_GROUP_ID=your_group_id_here

# Name of the Discord category to monitor (default: papers)
PAPERS_CATEGORY_NAME=papers

# Default number of messages scanned per channel by /scan_papers (default: 100)
MAX_MESSAGES_PER_CHANNEL=500
```

---

## Step 6 — Set up your Discord server

1. In your Discord server, create a **Category** with the same name as `PAPERS_CATEGORY_NAME` (default: `papers`)
2. Add one or more text channels inside it — for example:
   - `#neuro`
   - `#ml`
   - `#general`

The bot monitors every text channel inside this category. The channel name is automatically applied as a tag on each Zotero item.

---

## Step 7 — Run the bot

```bash
uv run zotero-bot.py
```

You should see log output confirming the bot is online:

```
zotero-bot#1234 is online!
Monitoring category: papers
Zotero Group ID: 6400311
```

---

## Step 8 — Test it

Post any paper link in one of your monitored channels:

```
https://arxiv.org/abs/2404.05553
```

Within a few seconds the bot should react with 🤖 and the paper will appear in your Zotero library with full metadata and a PDF attachment (or linked URL for Public Open groups).

---

## Step 9 — Backfill existing channel history (optional)

If you already have paper links posted in your channels, use the `/scan_papers` slash command to import them all:

- `/scan_papers` — scans up to `MAX_MESSAGES_PER_CHANNEL` messages per channel
- `/scan_papers all_messages:True` — scans every message in each channel with no limit

The command reports how many papers were added, how many were already in the library, and any errors.

---

## Troubleshooting

### Bot does not respond to messages

- Confirm **Message Content Intent** is enabled in the Developer Portal (Step 1)
- Confirm the bot has **Read Messages** and **Read Message History** permissions in the monitored category
- Check that the category name in your server matches `PAPERS_CATEGORY_NAME` exactly (case-insensitive)

### Papers are not being added

- Check the bot logs for error messages
- Confirm your Zotero API key has **Write** access for the group
- Try `/zotero_stats` to verify the Zotero connection is working

### PDFs are not attaching (Public Open group)

- Public Open groups cannot store files — this is a Zotero platform limitation
- The bot automatically attaches a linked URL instead; no action needed
- If you want stored PDFs, change the group type to Private or Public Closed in your [Zotero group settings](https://www.zotero.org/groups)

### SSL errors on startup

The bot requires Python's SSL library to have access to a valid CA bundle. If you see `SSL: CERTIFICATE_VERIFY_FAILED` errors, `certifi` is already listed as a dependency — run `uv sync` to make sure it is installed.

---

## Further reading

- [README.md](README.md) — feature overview and configuration reference
- [docs/index.md](docs/index.md) — full documentation index
- [docs/pdf_attachments.md](docs/pdf_attachments.md) — PDF storage behavior and Public Open group notes
- [docs/duplicate_detection.md](docs/duplicate_detection.md) — how duplicate checking works
- [docs/troubleshooting_pdf_attachments.md](docs/troubleshooting_pdf_attachments.md) — PDF troubleshooting
- [CHANGELOG.md](CHANGELOG.md) — version history
