# Zotero Discord Bot

A Discord bot that automatically monitors channels in a "papers" category and adds linked articles to a Zotero group library.

## Features

- 🤖 **Real-time Monitoring**: Automatically detects paper links posted in channels under the "papers" category
- 🔗 **Multi-format Support**: Handles DOIs, arXiv links, PubMed links, PDF URLs, and generic scholarly URLs (Nature, Science, etc.)
- ✅ **Duplicate Detection**: Checks for existing papers and reacts with different emojis
- 📚 **Backfill Command**: `/scan_papers` command to process existing messages
- 📊 **Statistics**: `/zotero_stats` command to view library statistics

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `DISCORD_TOKEN`: Your Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- `ZOTERO_TOKEN`: Your Zotero API token from [Zotero Settings](https://www.zotero.org/settings/keys)
- `ZOTERO_GROUP_ID`: Your Zotero group ID (found in your group library URL)

### 3. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Enable "Message Content Intent" under Privileged Gateway Intents
5. Copy the bot token to your `.env` file
6. Invite the bot to your server with these permissions:
   - Read Messages/View Channels
   - Send Messages
   - Add Reactions
   - Read Message History

### 4. Create Papers Category

In your Discord server:
1. Create a category called "papers" (or customize with `PAPERS_CATEGORY_NAME`)
2. Create channels under this category for different topics
3. The bot will monitor all channels in this category

### 5. Run the Bot

```bash
uv run python zotero-bot.py
```

## Usage

### Automatic Monitoring

Simply post paper links in any channel under the "papers" category:

- DOI: `https://doi.org/10.1038/s41591-025-04133-4`
- arXiv: `https://arxiv.org/abs/2401.12345`
- PubMed: `https://pubmed.ncbi.nlm.nih.gov/12345678/`
- Generic URL: `https://www.nature.com/articles/s41591-025-04133-4`

The bot will:
- 🤖 React with a robot emoji when successfully added
- ✅ React with a checkmark emoji if already in library

### Commands

#### `/scan_papers`
Scans existing messages in all "papers" category channels and adds papers to Zotero.

Options:
- `limit`: Maximum messages to scan per channel (default: 100)

Example:
```
/scan_papers limit:200
```

#### `/zotero_stats`
Displays statistics about your Zotero library:
- Total items
- Number of collections
- Group ID

## Supported Link Types

1. **DOI**: `doi.org/10.xxxx`, `dx.doi.org/10.xxxx`, or bare DOIs
2. **arXiv**: `arxiv.org/abs/xxxx`, `arxiv.org/pdf/xxxx`
3. **PubMed**: `pubmed.ncbi.nlm.nih.gov/xxxxx`, or `PMID: xxxxx`
4. **PDF URLs**: Direct links to PDF files
5. **Generic URLs**: Any scholarly website (Nature, Science, journal sites, etc.)

## Configuration

Environment variables in `.env`:

- `PAPERS_CATEGORY_NAME`: Category name to monitor (default: "papers")
- `MAX_MESSAGES_PER_CHANNEL`: Default limit for `/scan_papers` command (default: 100)

## Logging

The bot logs important events to console:
- Paper additions
- Duplicate detections
- Errors and warnings

## Tutorial

Original Discord bot tutorial: https://youtu.be/9-rq5PqFXAw?si=MGv8FJCFEl5B3pap
