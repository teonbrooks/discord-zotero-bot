# bioRxiv Support

## Overview

The bot now supports bioRxiv preprints, following the same pattern as arXiv support. bioRxiv is a preprint server for biology papers, similar to arXiv but specifically for biological sciences.

## Features

### Automatic Detection

The bot automatically detects bioRxiv links in the following formats:

1. **bioRxiv content URLs**:
   - `https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1`
   - `https://biorxiv.org/content/10.1101/2023.05.15.540123`

2. **DOI URLs**:
   - `https://doi.org/10.1101/2023.05.15.540123`

3. **Bare DOIs**:
   - `10.1101/2023.05.15.540123`
   - `10.1101/2023.05.15.540123v2` (with version)

### Metadata Extraction

The bot fetches complete metadata from the bioRxiv API, including:

- **Title**: Full paper title
- **Authors**: All author names (properly formatted)
- **Abstract**: Complete abstract (cleaned of HTML/XML tags)
- **DOI**: bioRxiv DOI (format: 10.1101/YYYY.MM.DD.XXXXXX)
- **Date**: Publication/posting date
- **Category**: Subject area (e.g., "Neuroscience", "Bioinformatics")
- **Version**: Version number (v1, v2, etc.)
- **URL**: Full link to bioRxiv page

### Item Type in Zotero

bioRxiv papers are added as **Preprint** items with:
- Repository: "bioRxiv"
- Archive ID: The DOI
- All standard metadata fields
- Tags: `discord-zotero-bot` + channel name

## How It Works

### Detection Priority

The bot checks links in this order:

1. **bioRxiv** (checked first, before general DOI check)
2. DOI (general)
3. arXiv
4. PubMed
5. PDF
6. Generic URL

**Why bioRxiv is checked first**: bioRxiv uses DOIs that start with `10.1101/`, so we need to detect bioRxiv specifically before doing a general DOI check. This ensures bioRxiv papers get proper preprint metadata instead of being processed as general DOI lookups.

### API Integration

The bot uses the bioRxiv REST API:
- Endpoint: `https://api.biorxiv.org/details/biorxiv/{DOI}`
- Returns JSON with complete metadata
- Handles versioned preprints (v1, v2, etc.)

### Metadata Processing

1. **Extract DOI** from URL or text
2. **Query bioRxiv API** with the DOI
3. **Parse response** and extract all fields
4. **Clean abstract** (remove HTML/XML tags)
5. **Format authors** (handles "Last, First" format)
6. **Check for duplicates** (DOI, URL, title)
7. **Create Zotero item** with all metadata

## Examples

### Example 1: bioRxiv URL

**Post in Discord**:
```
Check out this paper: https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1
```

**Bot actions**:
1. Detects bioRxiv DOI: `10.1101/2023.05.15.540123v1`
2. Fetches metadata from bioRxiv API
3. Creates preprint in Zotero with:
   - Title: (fetched from API)
   - Authors: (all authors properly formatted)
   - Abstract: (clean, no HTML tags)
   - Repository: bioRxiv
   - DOI: 10.1101/2023.05.15.540123v1
   - Tags: discord-zotero-bot, [channel-name]
4. Reacts with 🤖

**Result in Zotero**:
```
Type: Preprint
Title: [Paper title from bioRxiv]
Authors: [All authors]
Repository: bioRxiv
Archive ID: 10.1101/2023.05.15.540123v1
DOI: 10.1101/2023.05.15.540123v1
Date: [Publication date]
Abstract: [Clean abstract text]
URL: https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1
Tags: discord-zotero-bot, [channel-name]
```

### Example 2: DOI Format

**Post in Discord**:
```
https://doi.org/10.1101/2023.05.15.540123
```

**Bot actions**:
- Recognizes `10.1101/` as bioRxiv DOI prefix
- Fetches from bioRxiv API (same as above)
- Creates preprint with full metadata

### Example 3: Bare DOI

**Post in Discord**:
```
Interesting paper: 10.1101/2023.05.15.540123
```

**Bot actions**:
- Extracts DOI from text
- Fetches from bioRxiv API
- Creates preprint with full metadata

## bioRxiv vs General DOI

### When is a DOI treated as bioRxiv?

A DOI is recognized as bioRxiv when:
- Starts with `10.1101/`
- Followed by date pattern: `YYYY.MM.DD.XXXXXX`
- Optional version suffix: `v1`, `v2`, etc.

### Example Comparison

**bioRxiv DOI**:
```
10.1101/2023.05.15.540123
         ↑
         Date pattern (YYYY.MM.DD)
```
→ Fetched from bioRxiv API as preprint

**Regular DOI**:
```
10.1038/s41591-025-04133-4
         ↑
         No date pattern
```
→ Fetched from CrossRef as journal article

## Author Name Handling

bioRxiv provides author names in various formats. The bot handles:

### Format 1: "Last, First"
```
Input: "Smith, John; Doe, Jane"
Output: 
  - firstName: "John", lastName: "Smith"
  - firstName: "Jane", lastName: "Doe"
```

### Format 2: "First Last"
```
Input: "John Smith; Jane Doe"
Output:
  - firstName: "John", lastName: "Smith"
  - firstName: "Jane", lastName: "Doe"
```

The bot intelligently detects commas and splits accordingly.

## Version Handling

bioRxiv papers often have multiple versions (v1, v2, etc.):

- **Version in URL**: Preserved in DOI and Archive ID
- **Latest version**: API returns most recent metadata
- **Version field**: Stored in metadata if provided

### Example:
```
URL: https://www.biorxiv.org/content/10.1101/2023.05.15.540123v2

Stored as:
- DOI: 10.1101/2023.05.15.540123v2
- Archive ID: 10.1101/2023.05.15.540123v2
- Version: v2 (if provided by API)
```

## Duplicate Detection

The bot checks for duplicates using:

1. **DOI matching** (primary)
2. **URL matching** (including biorxiv.org URLs)
3. **Title matching** (fallback)

### Example Duplicate Scenario

**First share**:
```
https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1
→ 🤖 Added
```

**Second share** (different format, same paper):
```
https://doi.org/10.1101/2023.05.15.540123
→ ✅ Duplicate detected via DOI
```

## Testing

Run the test suite to verify bioRxiv extraction:

```bash
cd /Users/teonbrooks/codespace/zotero-bot
python test_biorxiv.py
```

**Expected output**:
```
SUMMARY: 7 passed, 0 failed out of 7 tests
```

## Comparison: bioRxiv vs arXiv

| Feature | bioRxiv | arXiv |
|---------|---------|-------|
| Domain | Biology | Physics, CS, Math |
| Identifier | DOI (10.1101/...) | arXiv ID (YYMM.NNNNN) |
| API | REST (JSON) | Atom/XML |
| Repository | bioRxiv | arXiv |
| Item type | Preprint | Preprint |
| Versioning | v1, v2, ... | v1, v2, ... |

Both are treated as preprints in Zotero with full metadata.

## Error Handling

### API Failures

If bioRxiv API is unavailable:
```python
logger.warning(f"bioRxiv API returned status {response.status_code} for DOI: {doi}")
return (False, "metadata_fetch_failed")
```

The bot logs the error and doesn't add the paper.

### Invalid DOIs

If a bioRxiv DOI doesn't exist:
- API returns empty collection
- Bot logs warning
- No item created

### Network Issues

- 30-second timeout on API calls
- Graceful error handling
- User sees no reaction (not 🤖 or ✅)

## Supported Journals via bioRxiv

bioRxiv hosts preprints across biological sciences:

- Neuroscience
- Bioinformatics
- Genomics
- Cell Biology
- Microbiology
- Immunology
- Evolutionary Biology
- And many more...

All are automatically detected and processed with full metadata.

## Usage Tips

### For Users

1. **Post any bioRxiv format**: URL, DOI, or bare DOI all work
2. **Version numbers**: Can include version (v1, v2) or not
3. **Wait for reaction**: 🤖 means added, ✅ means duplicate
4. **Check Zotero**: Paper appears as Preprint with bioRxiv repository

### For Developers

1. **API Documentation**: https://api.biorxiv.org/
2. **Pattern matching**: See `extract_biorxiv_doi()` function
3. **Metadata parsing**: See `fetch_biorxiv_metadata()` function
4. **Integration**: bioRxiv added to `categorize_link()` and `add_to_zotero_by_identifier()`

## Future Enhancements

Possible improvements:

1. **medRxiv support**: Same API, different domain (medical preprints)
2. **Category-based tagging**: Add subject category as Zotero tag
3. **Citation tracking**: Track if preprint was later published
4. **Author disambiguation**: Better name parsing for complex formats
5. **Related preprints**: Link to other versions

## Troubleshooting

### bioRxiv link not detected

**Check**:
- DOI format correct? (10.1101/YYYY.MM.DD.XXXXXX)
- URL includes "biorxiv.org"?
- Run test: `python test_biorxiv.py`

### No metadata fetched

**Check**:
- DOI exists on bioRxiv?
- API available? (test manually: `https://api.biorxiv.org/details/biorxiv/10.1101/2023.05.15.540123`)
- Network connection working?
- Check logs for error messages

### Paper added as wrong type

**If added as DOI instead of bioRxiv**:
- Check detection order in code
- bioRxiv should be checked before general DOI
- Verify DOI matches bioRxiv pattern

## Summary

✅ **Full bioRxiv support** following arXiv pattern
✅ **Multiple URL formats** detected automatically  
✅ **Complete metadata** from bioRxiv API  
✅ **Clean abstracts** with HTML/XML stripped  
✅ **Proper preprint** item type in Zotero  
✅ **Automatic tagging** with bot + channel tags  
✅ **Duplicate detection** via DOI/URL/title  
✅ **Version handling** for v1, v2, etc.  
✅ **Comprehensive testing** with 7 test cases  

The bot now seamlessly handles both arXiv (physical sciences) and bioRxiv (biological sciences) preprints! 🧬
