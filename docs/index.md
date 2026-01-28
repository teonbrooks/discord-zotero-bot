# Zotero Discord Bot - Documentation Index

Complete documentation for the Zotero Discord Bot, organized by topic.

## 📚 Quick Start

- **[Main README](../README.md)** - Setup, installation, and basic usage
- **[Testing Guide](testing.md)** - How to test the bot

## 🔗 Paper Source Support

Documentation for each supported paper source (located in [`support/`](support/)):

### Published Articles
- **[DOI / CrossRef](support/doi_crossref_support.md)** - Published articles via DOI
  - Most comprehensive metadata
  - All major publishers
  - Full abstracts

### Preprint Servers
- **[arXiv](support/arxiv_troubleshooting.md)** - Physics, CS, Math preprints
  - arXiv DOI format support
  - Complete metadata
  - Categories and versions

- **[bioRxiv](support/biorxiv_support.md)** - Biology preprints
  - DOI-based (10.1101/*)
  - Full metadata
  - Version tracking

### Databases
- **[PubMed](support/pubmed_support.md)** - Biomedical literature
  - 40+ million citations
  - PMID support
  - DOI integration

## 🛠️ Features & Technical Docs

### Core Features
- **[Metadata Extraction](metadata_improvements.md)** - How metadata is fetched and processed
- **[Duplicate Detection](duplicate_detection.md)** - Preventing duplicate entries
- **[Tagging & Abstracts](tagging_and_abstracts.md)** - Automatic tagging and abstract cleaning
- **[PDF Attachments](pdf_attachments.md)** - Automatic PDF download and attachment

### Troubleshooting
- **[Debugging Duplicates](debugging_duplicates.md)** - Diagnosing duplicate issues
- **[arXiv Troubleshooting](support/arxiv_troubleshooting.md)** - Specific arXiv issues

## 📊 Comparison Table

| Source | Type | Coverage | Metadata Quality | Abstracts | Special Features |
|--------|------|----------|-----------------|-----------|------------------|
| **DOI/CrossRef** | Published | All disciplines | ⭐⭐⭐⭐⭐ | Full | Most complete |
| **arXiv** | Preprints | Physics, CS, Math | ⭐⭐⭐⭐ | Full | Categories, versions |
| **bioRxiv** | Preprints | Biology | ⭐⭐⭐⭐ | Full | Biology focus |
| **PubMed** | Database | Biomedical | ⭐⭐⭐ | Limited | 40M+ citations |

## 🎯 Use Cases

### For Researchers
1. Share papers in Discord → Auto-added to Zotero
2. Track papers by channel/topic
3. Build research library collaboratively
4. Discover papers shared by community

### For Research Groups
1. Organize papers by project (Discord channels)
2. Automatic tagging by source
3. No manual entry needed
4. Shared group library

### For Journal Clubs
1. Members share papers via links
2. Auto-populate reading list
3. Track discussion topics
4. Maintain paper archive

## 🔢 Supported Link Formats

### DOI
```
https://doi.org/10.1038/s41591-025-04133-4
10.1038/s41591-025-04133-4
```

### arXiv
```
https://arxiv.org/abs/2404.05553
https://doi.org/10.48550/arXiv.2404.05553
2404.05553
```

### bioRxiv
```
https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1
https://doi.org/10.1101/2023.05.15.540123
10.1101/2023.05.15.540123
```

### PubMed
```
https://pubmed.ncbi.nlm.nih.gov/38180801/
PMID: 38180801
```

### Generic URLs
```
https://www.nature.com/articles/s41591-025-04133-4
(Any scholarly website with metadata)
```

## ⚙️ Architecture

### Bot Flow
```
Discord Message
    ↓
Extract URLs
    ↓
Categorize Link Type
    ↓
Fetch Metadata (API)
    ↓
Check Duplicates
    ↓
Clean & Format
    ↓
Add to Zotero
    ↓
React with Emoji
```

### Detection Priority
1. arXiv (including DOI format)
2. bioRxiv (DOI: 10.1101/*)
3. DOI (general)
4. PubMed
5. PDF
6. Generic URL

## 🏷️ Automatic Features

### Tagging
Every paper gets:
- `discord-zotero-bot` tag
- Channel name tag (e.g., `machine-learning`)

### Abstract Cleaning
- Removes HTML/XML tags
- Removes title tags
- Clean, readable text

### Duplicate Prevention
- Checks DOI, URL, title
- Reacts with ✅ if duplicate
- Reacts with 🤖 if new

## 📝 File Organization

```
zotero-bot/
├── zotero-bot.py           # Main bot code
├── README.md               # Quick start guide
├── pyproject.toml          # Dependencies
├── .env.example            # Config template
├── docs/                   # 📚 All documentation
│   ├── INDEX.md           # This file
│   ├── DOI_CROSSREF_SUPPORT.md
│   ├── ARXIV_TROUBLESHOOTING.md
│   ├── BIORXIV_SUPPORT.md
│   ├── PUBMED_SUPPORT.md
│   ├── METADATA_IMPROVEMENTS.md
│   ├── DUPLICATE_DETECTION.md
│   ├── TAGGING_AND_ABSTRACTS.md
│   ├── DEBUGGING_DUPLICATES.md
│   └── TESTING.md
└── tests/                  # 🧪 Test scripts
    ├── test_arxiv_live.py
    ├── test_biorxiv.py
    ├── test_abstract_cleaning.py
    └── test_duplicates.py
```

## 🧪 Testing

### Test Scripts
Located in `tests/` directory:

- **test_arxiv_live.py** - Test arXiv API and detection
- **test_biorxiv.py** - Test bioRxiv detection patterns
- **test_abstract_cleaning.py** - Test HTML/XML cleaning
- **test_duplicates.py** - Test duplicate detection

### Running Tests
```bash
cd tests
uv run python test_arxiv_live.py
uv run python test_biorxiv.py
uv run python test_abstract_cleaning.py
```

## 🔍 Debugging

### Enable Debug Logging
Edit `zotero-bot.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check Logs
Look for these patterns:
```
INFO - Detected [type] link with ID: [id]
INFO - Processing [type] paper with ID: [id]
INFO - Successfully fetched [type] metadata
INFO - Added item with [type] and metadata
```

### Common Issues
1. **Link not detected** → Check URL format in source-specific docs
2. **Metadata missing** → Check API availability
3. **Duplicates created** → See [Debugging Duplicates](debugging_duplicates.md)
4. **No reaction** → Check bot permissions

## 🚀 Future Enhancements

### Planned Features
- [ ] medRxiv support (medical preprints)
- [ ] SSRN support (social sciences)
- [ ] PubMed Central full-text links
- [ ] MeSH terms as tags
- [ ] Citation tracking
- [ ] Related papers suggestions
- [ ] Export collections by channel
- [ ] Statistics dashboard

### Community Contributions
See issues on GitHub for ways to contribute.

## 📞 Support

### Getting Help
1. Check relevant source documentation
2. Review troubleshooting guides
3. Enable debug logging
4. Check test scripts
5. Report issues with:
   - Exact URL tried
   - Console logs
   - Expected vs actual behavior

### Reporting Bugs
Include:
- Bot version
- URL that failed
- Console output
- Steps to reproduce
- Expected behavior

## 📄 License & Credits

### Dependencies
- **discord.py** - Discord API
- **pyzotero** - Zotero API
- **httpx** - HTTP client
- **python-dotenv** - Environment config

### APIs Used
- CrossRef REST API
- arXiv API
- bioRxiv API
- NCBI E-utilities
- Zotero Web API

### Acknowledgments
- CrossRef for open metadata
- arXiv for preprint access
- NCBI for PubMed
- bioRxiv for biology preprints
- Zotero for reference management

## 📚 External Resources

### Documentation
- [Zotero API Docs](https://www.zotero.org/support/dev/web_api/v3/start)
- [discord.py Docs](https://discordpy.readthedocs.io/)
- [CrossRef API](https://api.crossref.org/)
- [arXiv API](https://arxiv.org/help/api/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)

### Community
- [Zotero Forums](https://forums.zotero.org/)
- [Discord Developer Portal](https://discord.com/developers/docs/)

---

**Need quick help?** Check the [Main README](../README.md) for setup and basic usage!
