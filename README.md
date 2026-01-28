# Zotero Discord Bot

A Discord bot that automatically monitors channels in a "papers" category and adds linked articles to a Zotero group library.

## Features

- 🤖 **Real-time Monitoring**: Automatically detects paper links posted in channels under the "papers" category
- 🔗 **Multi-format Support**: Handles DOIs, arXiv links, PubMed links, PDF URLs, and generic scholarly URLs (Nature, Science, etc.)
- 📝 **Rich Metadata Extraction**: Automatically fetches complete metadata including:
  - **DOIs**: Full bibliographic data from CrossRef (title, authors, journal, volume, issue, pages, clean abstract)
  - **arXiv**: Complete preprint metadata (title, authors, abstract, categories, publication date)
  - **bioRxiv**: Complete preprint metadata (title, authors, abstract, DOI, publication date)
  - **PubMed**: Journal article details (title, authors, journal, volume, issue, pages, DOI if available)
  - **Generic URLs**: Attempts to extract metadata from webpage meta tags
  - **Clean Abstracts**: Automatically strips XML/HTML tags from abstracts
- 📄 **PDF Attachments**: Automatically downloads and attaches PDFs when freely available:
  - **arXiv**: All papers (100% coverage)
  - **bioRxiv**: All papers (100% coverage)
  - **DOI**: Open access papers when available
  - Respects copyright - only downloads freely available PDFs
- 🏷️ **Automatic Tagging**: Every paper added gets tagged with:
  - `discord-zotero-bot` - identifies items added by the bot
  - Channel name (e.g., `machine-learning`, `neuroscience`) - tracks where papers were shared
- ✅ **Smart Duplicate Detection**: Comprehensive checking across DOI, URL, and title to prevent duplicates
  - Handles URL variations (http/https, trailing slashes)
  - Recognizes same paper from different sources (e.g., DOI URL vs journal URL)
  - Checks up to 50 items for reliable detection in larger libraries
- 📚 **Backfill Command**: `/scan_papers` command to process existing messages
- 📎 **PDF Backfill**: `/attach_pdfs` command to attach PDFs to existing items without them
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
- bioRxiv: `https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1`
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

#### `/attach_pdfs`
Scans existing Zotero items and attaches PDFs where available.

Options:
- `limit`: Maximum number of items to process (default: 50, max: 200)

**What it does**:
- Checks each item in your library for existing PDF attachments
- Skips items that already have PDFs
- Extracts identifiers (DOI, arXiv ID, bioRxiv DOI) from items
- Attempts to download and attach PDFs for items without them
- Works for: arXiv (100%), bioRxiv (100%), open access DOIs (when available)

**Example**:
```
/attach_pdfs limit:100
```

**Use cases**:
- Backfill PDFs for papers added before PDF attachment feature
- Retry PDF downloads that previously failed
- Add PDFs to manually created items

#### `/zotero_stats`
Displays statistics about your Zotero library:
- Total items
- Number of collections
- Group ID

## Supported Link Types & Metadata

📚 **Comprehensive documentation available in the [`docs/`](docs/) folder!**

- **[Documentation Index](docs/index.md)** - Complete documentation overview
- **[DOI/CrossRef](docs/support/doi_crossref_support.md)** - Published articles
- **[arXiv](docs/support/arxiv_troubleshooting.md)** - Physics, CS, Math preprints
- **[bioRxiv](docs/support/biorxiv_support.md)** - Biology preprints
- **[PubMed](docs/support/pubmed_support.md)** - Biomedical literature

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
**Formats**: 
- Standard: `arxiv.org/abs/xxxx`, `arxiv.org/pdf/xxxx`
- DOI format: `doi.org/10.48550/arXiv.xxxx` (NEW!)
- Bare IDs: `2401.12345`

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

### 3. bioRxiv Links
**Formats**: `biorxiv.org/content/10.1101/YYYY.MM.DD.XXXXXX`, or DOI `10.1101/YYYY.MM.DD.XXXXXX`

**Metadata Source**: bioRxiv API

**Extracted Fields**:
- Title
- Authors
- Abstract
- DOI
- Publication date
- Category/Subject
- Version
- URL

### 4. PubMed Links
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

### 5. PDF URLs
**Formats**: Direct links ending in `.pdf`

**Behavior**: Creates an attachment item in Zotero

### 6. Generic Scholarly URLs
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

## Automatic Tagging

Every paper added to your Zotero library is automatically tagged with:

### Bot Tag
**`discord-zotero-bot`** - Applied to all items added by the bot

This makes it easy to:
- Filter for bot-added papers in Zotero
- See how many papers the bot has added
- Distinguish bot imports from manual additions

### Channel Tag
**Channel name** (e.g., `machine-learning`, `papers-to-read`, `neuroscience`)

This helps you:
- Track which Discord channel a paper came from
- Organize papers by topic/community
- Find papers shared in specific channels

### Example in Zotero

When you add a paper from the `#machine-learning` channel:

```
Title: A multimodal sleep foundation model for disease prediction
Tags: discord-zotero-bot, machine-learning
```

### Filtering by Tags in Zotero

- Click on a tag to see all papers with that tag
- Use tag colors to highlight important channels
- Search for `discord-zotero-bot` to see all bot-added papers
- Combine tags: e.g., show all papers from `machine-learning` channel

## Logging

The bot logs important events to console:
- Paper additions
- Duplicate detections (with what matched)
- Errors and warnings

## Tutorial

Original Discord bot tutorial: https://youtu.be/9-rq5PqFXAw?si=MGv8FJCFEl5B3pap
