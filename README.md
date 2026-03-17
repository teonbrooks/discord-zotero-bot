# Zotero Discord Bot

A Discord bot that automatically monitors channels in a "papers" category and adds linked articles to a Zotero group library.

---

## Features

- 🤖 **Real-time monitoring** — automatically detects paper links posted in channels under the `papers` category
- 🔗 **Multi-format support** — handles arXiv, bioRxiv, DOIs, PubMed IDs, PDF URLs, and generic scholarly URLs
- 📝 **Rich metadata extraction** — fetches complete bibliographic data from source APIs:
  - **DOIs**: title, authors, journal, volume, issue, pages, clean abstract (CrossRef)
  - **arXiv**: title, authors, abstract, categories, publication date
  - **bioRxiv**: title, authors, abstract, DOI, publication date
  - **PubMed**: title, authors, journal, volume, issue, pages, DOI
  - **Generic URLs**: extracts metadata from HTML citation meta tags
- 📄 **PDF attachments** — automatically downloads and attaches PDFs when freely available:
  - arXiv: 100% coverage
  - bioRxiv: 100% coverage
  - DOIs: open-access papers when available
  - Falls back to a linked URL for Public Open groups or unavailable PDFs
- 🏷️ **Automatic tagging** — every item gets tagged with `discord-zotero-bot` and the source channel name
- ✅ **Duplicate detection** — checks DOI, URL, and title before adding to keep the library clean
- 📚 **Backfill** — `/scan_papers` retroactively processes existing channel history, with an option to scan all messages
- 📎 **PDF backfill** — `/attach_pdfs` attaches PDFs to existing Zotero items that are missing them
- 📊 **Library stats** — `/zotero_stats` shows a quick summary of the connected library

---

## Usage

### Automatic monitoring

Post any paper link in a channel inside the monitored category:

```
https://doi.org/10.1038/s41591-025-04133-4
https://arxiv.org/abs/2401.12345
https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1
https://pubmed.ncbi.nlm.nih.gov/12345678/
https://www.nature.com/articles/s41591-025-04133-4
```

The bot reacts to the message within seconds:
- 🤖 — paper added successfully
- ✅ — already in the library (duplicate)

### Slash commands

#### `/scan_papers [limit] [all_messages]`

Retroactively scans all channels in the monitored category and adds any papers not yet in Zotero.

- `limit` — max messages per channel (1–10000, default from `MAX_MESSAGES_PER_CHANNEL`). Ignored when `all_messages` is enabled.
- `all_messages` — set to `True` to scan every message with no upper limit (default: `False`)

```
/scan_papers limit:500
/scan_papers all_messages:True
```

#### `/attach_pdfs [limit]`

Scans existing Zotero items and attaches PDFs to those that are missing them. Works for arXiv, bioRxiv, and open-access DOIs.

- `limit` — max items to process (default: 50, max: 200)

```
/attach_pdfs limit:100
```

#### `/zotero_stats`

Displays the total item count, number of collections, and group ID for the connected library.

---

## Supported link types

| Type | Formats | Metadata source | PDF |
|------|---------|-----------------|-----|
| **arXiv** | `arxiv.org/abs/...`, bare IDs, `10.48550/arXiv.*` DOIs | arXiv API | ✅ Always |
| **bioRxiv** | `biorxiv.org/content/...`, `10.1101/` DOIs | bioRxiv API | ✅ Always |
| **DOI** | `doi.org/...`, `dx.doi.org/...`, bare `10.xxxx/...` | CrossRef API | ✅ Open access |
| **PubMed** | `pubmed.ncbi.nlm.nih.gov/...`, `PMID: ...` | PubMed eUtils | ❌ |
| **Generic URL** | Any `http(s)://` link | HTML meta tags | ❌ |

For detailed notes on each source see the [`docs/support/`](docs/support/) folder.

---

## PDF attachment behavior

For libraries that support file storage, the bot stores a full PDF copy. For libraries that do not (e.g. Zotero Public Open groups), or when a PDF is unavailable, it automatically attaches a linked URL instead — no configuration needed.

| Library type | File storage | PDF behavior |
|---|---|---|
| Private group | ✅ | Full PDF stored |
| Public Closed group | ✅ | Full PDF stored |
| **Public Open group** | ❌ | Linked URL attached |

See [docs/pdf_attachments.md](docs/pdf_attachments.md) for more detail.

---

## Duplicate detection

Before adding any item, the bot runs a three-stage check:

1. **DOI** match (most reliable)
2. **URL** match (with http/https and trailing-slash normalization)
3. **Title** match (exact, case-insensitive)

```
First:  https://doi.org/10.1038/s41591-025-04133-4       → 🤖 Added
Second: https://www.nature.com/articles/s41591-025-04133-4 → ✅ Duplicate
```

See [docs/duplicate_detection.md](docs/duplicate_detection.md) for more detail.

---

## Auto-tagging

Every item gets two tags:

- `discord-zotero-bot` — marks the item as bot-sourced; filter in Zotero to see everything the bot has added
- `<channel-name>` — records which Discord channel the link came from (e.g. `machine-learning`, `neuroscience`)

See [docs/tagging_and_abstracts.md](docs/tagging_and_abstracts.md) for more detail.

---

## Setup

See **[GETTING_STARTED.md](GETTING_STARTED.md)** for a complete step-by-step guide covering Discord bot creation, Zotero API key setup, and first-run instructions.

### Quick start

```bash
# Install dependencies
uv sync

# Configure credentials
cp .env.example .env   # then fill in your values

# Run
uv run zotero-bot.py
```

### Configuration reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | ✅ | — | Discord bot token |
| `ZOTERO_TOKEN` | ✅ | — | Zotero API key |
| `ZOTERO_GROUP_ID` | ✅ | — | Zotero group library ID |
| `PAPERS_CATEGORY_NAME` | | `papers` | Discord category name to monitor |
| `MAX_MESSAGES_PER_CHANNEL` | | `100` | Default scan depth for `/scan_papers` |

---

## Documentation

Full docs live in the [`docs/`](docs/) folder:

- [docs/index.md](docs/index.md) — documentation index
- [docs/pdf_attachments.md](docs/pdf_attachments.md) — PDF attachment behavior
- [docs/duplicate_detection.md](docs/duplicate_detection.md) — how duplicate checking works
- [docs/tagging_and_abstracts.md](docs/tagging_and_abstracts.md) — tagging and abstract cleaning
- [docs/support/](docs/support/) — per-source guides (DOI, arXiv, bioRxiv, PubMed)
- [docs/troubleshooting_pdf_attachments.md](docs/troubleshooting_pdf_attachments.md) — PDF troubleshooting
- [CHANGELOG.md](CHANGELOG.md) — version history
