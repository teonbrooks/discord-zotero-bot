# Zotero Discord Bot

A Discord bot that automatically monitors channels in a "papers" category and adds linked articles to a Zotero group library.

## Features

- 🤖 **Real-time Monitoring**: Automatically detects paper links posted in channels under the "papers" category
- 🔗 **Multi-format Support**: Handles DOIs, arXiv links, PubMed links, PDF URLs, and generic scholarly URLs (Nature, Science, etc.)
- 📝 **Rich Metadata Extraction**: Automatically fetches complete metadata including:
  - **DOIs**: Full bibliographic data from CrossRef (title, authors, journal, volume, issue, pages, abstract)
  - **arXiv**: Complete preprint metadata (title, authors, abstract, categories, publication date)
  - **PubMed**: Journal article details (title, authors, journal, volume, issue, pages, DOI if available)
  - **Generic URLs**: Attempts to extract metadata from webpage meta tags
- ✅ **Smart Duplicate Detection**: Comprehensive checking across DOI, URL, and title to prevent duplicates
  - Handles URL variations (http/https, trailing slashes)
  - Recognizes same paper from different sources (e.g., DOI URL vs journal URL)
  - Checks up to 50 items for reliable detection in larger libraries
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

## Supported Link Types & Metadata

### 1. DOI Links
**Formats**: `doi.org/10.xxxx`, `dx.doi.org/10.xxxx`, or bare DOIs like `10.xxxx/yyyy`

**Metadata Source**: CrossRef API

**Extracted Fields**:
- Title
- Authors (first and last names)
- Journal/Publication title
- Volume, Issue, Pages
- Publication date
- Abstract
- DOI
- URL

### 2. arXiv Links
**Formats**: `arxiv.org/abs/xxxx`, `arxiv.org/pdf/xxxx`, or bare IDs like `2401.12345`

**Metadata Source**: arXiv API

**Extracted Fields**:
- Title
- Authors
- Abstract
- Publication date
- Categories
- arXiv ID
- DOI (if available)
- URL

### 3. PubMed Links
**Formats**: `pubmed.ncbi.nlm.nih.gov/xxxxx`, or `PMID: xxxxx`

**Metadata Source**: NCBI PubMed API

**Extracted Fields**:
- Title
- Authors
- Journal name
- Volume, Issue, Pages
- Publication date
- DOI (if available)
- URL

### 4. PDF URLs
**Formats**: Direct links ending in `.pdf`

**Behavior**: Creates an attachment item in Zotero

### 5. Generic Scholarly URLs
**Examples**: 
- `https://www.nature.com/articles/s41591-025-04133-4`
- Journal websites
- Institutional repositories

**Metadata Source**: HTML meta tags (citation metadata)

**Extracted Fields**:
- Title
- Authors (from citation_author meta tags)
- Journal (from citation_journal_title meta tag)
- DOI (if found, will use CrossRef for full metadata)
- Publication date
- URL

**Note**: For Nature articles and other major publishers, the bot will extract the DOI from the page and use CrossRef to get complete metadata.

## Configuration

Environment variables in `.env`:

- `PAPERS_CATEGORY_NAME`: Category name to monitor (default: "papers")
- `MAX_MESSAGES_PER_CHANNEL`: Default limit for `/scan_papers` command (default: 100)

## Duplicate Detection

The bot uses comprehensive duplicate detection to prevent the same paper from being added multiple times:

### How It Works
1. **DOI Matching**: Checks if the DOI already exists (most reliable)
2. **URL Matching**: Checks URLs with normalization (handles http/https, trailing slashes)
3. **Title Matching**: Checks paper titles as fallback

### Example Scenarios

**Same paper, different URLs**:
```
First: https://doi.org/10.1038/s41591-025-04133-4 → 🤖 Added
Second: https://www.nature.com/articles/s41591-025-04133-4 → ✅ Duplicate detected
```

**URL variations**:
```
First: https://example.com/paper → 🤖 Added
Second: http://example.com/paper/ → ✅ Duplicate detected
```

The bot will react with ✅ when a duplicate is detected, indicating the paper is already in your library.

For more details, see [DUPLICATE_DETECTION.md](DUPLICATE_DETECTION.md).

## Logging

The bot logs important events to console:
- Paper additions
- Duplicate detections (with what matched)
- Errors and warnings

## Tutorial

Original Discord bot tutorial: https://youtu.be/9-rq5PqFXAw?si=MGv8FJCFEl5B3pap
