# Project Structure

Complete organization of the Zotero Discord Bot project.

## Directory Layout

```
zotero-bot/
│
├── 📄 zotero-bot.py              # Main bot implementation
├── 📄 README.md                  # Quick start guide
├── 📄 pyproject.toml             # Project dependencies
├── 📄 uv.lock                    # Locked dependencies
├── 📄 .env.example               # Environment config template
├── 📄 .env                       # Your config (gitignored)
├── 📄 .gitignore                 # Git ignore rules
│
├── 📁 docs/                      # 📚 Documentation
│   ├── index.md                  # Documentation index (START HERE)
│   ├── project_structure.md      # This file
│   │
│   ├── 🛠️ Features & Technical
│   ├── metadata_improvements.md  # Metadata extraction
│   ├── duplicate_detection.md    # Duplicate prevention
│   ├── debugging_duplicates.md   # Troubleshooting duplicates
│   ├── tagging_and_abstracts.md  # Auto-tagging & cleaning
│   ├── testing.md                # Testing guide
│   │
│   └── 📁 support/               # 🔗 Paper Source Support Docs
│       ├── doi_crossref_support.md   # Published articles via DOI
│       ├── arxiv_troubleshooting.md  # arXiv preprints
│       ├── biorxiv_support.md        # bioRxiv preprints
│       └── pubmed_support.md         # PubMed database
│
└── 📁 tests/                     # 🧪 Test Suite
    ├── README.md                 # Test documentation
    ├── test_arxiv_live.py        # arXiv API tests
    ├── test_biorxiv.py           # bioRxiv pattern tests
    ├── test_abstract_cleaning.py # HTML/XML cleaning tests
    └── test_duplicates.py        # Duplicate detection tool
```

## Core Files

### `zotero-bot.py`
**Purpose**: Main bot implementation  
**Size**: ~1,700 lines  
**Contains**:
- Discord event handlers (`on_message`, `on_ready`)
- Slash commands (`/scan_papers`, `/zotero_stats`)
- Link detection & categorization
- Metadata fetchers (DOI, arXiv, bioRxiv, PubMed)
- Duplicate detection logic
- Zotero integration
- Abstract cleaning
- Auto-tagging

**Key Functions**:
```python
extract_doi()           # Extract DOI from URL/text
extract_arxiv_id()      # Extract arXiv ID
extract_biorxiv_doi()   # Extract bioRxiv DOI
extract_pubmed_id()     # Extract PMID
categorize_link()       # Determine link type
fetch_*_metadata()      # Fetch metadata from APIs
check_duplicate_comprehensive()  # Check for duplicates
strip_html_tags()       # Clean abstracts
add_to_zotero_*()       # Add to Zotero
```

### `pyproject.toml`
**Purpose**: Dependency management  
**Package Manager**: uv (fast Python package installer)  
**Dependencies**:
- `discord.py` - Discord bot framework
- `pyzotero` - Zotero API client
- `httpx` - HTTP client for API calls
- `beautifulsoup4` - HTML parsing
- `python-dotenv` - Environment variables

### `README.md`
**Purpose**: Quick start guide  
**Contains**:
- Installation instructions
- Bot setup (Discord & Zotero)
- Usage examples
- Feature overview
- Links to detailed docs

### `.env.example`
**Purpose**: Configuration template  
**Required Variables**:
```bash
DISCORD_TOKEN=your_discord_bot_token
ZOTERO_TOKEN=your_zotero_api_key
ZOTERO_GROUP_ID=your_group_id
```

## Documentation (`docs/`)

### Overview
- **10 documentation files** covering all aspects
- **Organized by topic**: sources (in `support/`), features, troubleshooting
- **Cross-referenced**: Easy navigation between docs
- **Start at**: `docs/index.md`

### Paper Source Docs (4 files)

#### `doi_crossref_support.md`
**Covers**: Published articles via DOI  
**Topics**:
- DOI format patterns
- CrossRef API integration
- Publisher coverage
- Metadata completeness
- Abstract cleaning
- Examples & troubleshooting

#### `arxiv_troubleshooting.md`
**Covers**: arXiv preprints  
**Topics**:
- arXiv ID formats
- arXiv DOI format (`10.48550/arXiv.*`)
- API integration
- Category system
- Version handling
- Common issues & solutions

#### `biorxiv_support.md`
**Covers**: bioRxiv biology preprints  
**Topics**:
- bioRxiv DOI format (`10.1101/*`)
- API integration
- Version tracking
- Detection patterns
- Examples & testing

#### `pubmed_support.md`
**Covers**: PubMed biomedical database  
**Topics**:
- PMID format
- E-utilities API
- Author name handling
- DOI integration
- Limitations & workarounds
- Future enhancements

### Feature Docs (4 files)

#### `metadata_improvements.md`
**Covers**: Metadata extraction system  
**Topics**:
- API integrations (CrossRef, arXiv, bioRxiv, PubMed)
- Webpage scraping
- Field mapping
- Quality improvements
- Before/after examples

#### `duplicate_detection.md`
**Covers**: How duplicates are prevented  
**Topics**:
- Detection strategies (DOI, URL, title)
- Normalization techniques
- Search scope & limits
- Fallback mechanisms
- Edge cases

#### `tagging_and_abstracts.md`
**Covers**: Auto-tagging and cleaning  
**Topics**:
- `discord-zotero-bot` tag
- Channel name tags
- HTML/XML tag removal
- Title tag stripping
- Whitespace normalization

#### `debugging_duplicates.md`
**Covers**: Troubleshooting duplicate issues  
**Topics**:
- Using test script
- Checking Zotero library
- Search verification
- Common causes
- Solutions

### Navigation & Testing (2 files)

#### `index.md` ⭐ START HERE
**Purpose**: Documentation hub  
**Contains**:
- Quick start links
- Topic organization
- Comparison tables
- Use cases
- Architecture overview
- File organization
- External resources

#### `testing.md`
**Purpose**: Testing guide  
**Contains**:
- Test scenarios
- Expected behaviors
- Manual testing steps
- Automated tests
- Verification procedures

#### `project_structure.md`
**Purpose**: This file!  
**Contains**:
- Directory layout
- File descriptions
- Organization rationale

## Tests (`tests/`)

### Overview
- **4 test scripts** for different components
- **1 README** documenting all tests
- **Mix of**: Unit tests, integration tests, interactive tools

### Test Files

#### `test_arxiv_live.py`
**Type**: Integration test  
**Requires**: Internet connection  
**Tests**:
- arXiv ID extraction
- arXiv DOI format
- API connectivity
- Metadata parsing
- 4 test cases with real papers

#### `test_biorxiv.py`
**Type**: Unit test  
**Requires**: Nothing (offline)  
**Tests**:
- bioRxiv DOI extraction
- URL pattern matching
- Version handling
- Edge cases
- 7 test cases

#### `test_abstract_cleaning.py`
**Type**: Unit test  
**Requires**: Nothing (offline)  
**Tests**:
- HTML tag removal
- XML tag removal
- JATS title removal
- Nested tags
- Whitespace cleanup
- 10 test cases

#### `test_duplicates.py`
**Type**: Interactive diagnostic tool  
**Requires**: Zotero API credentials  
**Features**:
- List recent library items
- Search by DOI
- Search by URL
- Verify duplicate detection
- Interactive menu

#### `tests/README.md`
**Purpose**: Test documentation  
**Contains**:
- Test descriptions
- How to run each test
- Expected results
- Troubleshooting
- Adding new tests

## Configuration Files

### `.env` (user-created, gitignored)
Your actual credentials - **NEVER commit this!**

### `.env.example` (committed)
Template showing required variables

### `.gitignore`
Excludes:
- `.env`
- `__pycache__/`
- `.venv/`
- IDE files

### `.python-version`
Specifies Python 3.12 for consistency

### `uv.lock`
Locked dependency versions for reproducibility

## Development Files

### `__pycache__/`
Python bytecode cache (gitignored)

### `.venv/`
Virtual environment (gitignored)

### `.git/`
Git repository data

## File Count Summary

```
Total: ~30 files

Code:
  - 1 main bot file (zotero-bot.py)
  - 4 test scripts
  - 1 test README

Documentation:
  - 1 main README
  - 10 doc files in docs/
  - 1 test README

Configuration:
  - 1 pyproject.toml
  - 1 .env.example
  - 1 .gitignore
  - 1 .python-version
  - 1 uv.lock
```

## Organization Rationale

### Why `docs/` folder?
- Keeps root clean
- Groups related documentation
- Easy to browse
- Professional structure

### Why `tests/` folder?
- Separates test from production code
- Makes testing clear
- Easy to run all tests
- Standard Python convention

### Why detailed per-source docs?
- Each source has unique quirks
- Makes troubleshooting easier
- Helps users understand coverage
- Documents API specifics

## Navigation Tips

### New Users
1. Start with `README.md`
2. Read `docs/index.md`
3. Check source-specific docs as needed

### Debugging Issues
1. Check relevant source doc (arXiv, bioRxiv, etc.)
2. Review `debugging_duplicates.md` for duplicates
3. Run relevant test script
4. Enable debug logging

### Contributing
1. Read `project_structure.md` (this file)
2. Review relevant docs
3. Check/add tests
4. Update documentation

## Quick Links

**Getting Started**:
- [Main README](../README.md)
- [Documentation Index](index.md)

**Paper Sources**:
- [DOI/CrossRef](support/doi_crossref_support.md)
- [arXiv](support/arxiv_troubleshooting.md)
- [bioRxiv](support/biorxiv_support.md)
- [PubMed](support/pubmed_support.md)

**Features**:
- [Metadata](metadata_improvements.md)
- [Duplicates](duplicate_detection.md)
- [Tagging](tagging_and_abstracts.md)

**Testing**:
- [Test Guide](testing.md)
- [Test README](../tests/README.md)

---

**Everything organized and documented!** 🎉
