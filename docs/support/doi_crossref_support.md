# DOI / CrossRef Support

## Overview

The bot supports DOI (Digital Object Identifier) links, fetching complete bibliographic metadata from the CrossRef API. CrossRef is the primary DOI registration agency for scholarly publications.

## Supported Formats

### 1. DOI URLs
```
https://doi.org/10.1038/s41591-025-04133-4
https://dx.doi.org/10.1038/s41591-025-04133-4
```

### 2. Bare DOIs
```
10.1038/s41591-025-04133-4
DOI: 10.1038/s41591-025-04133-4
```

### 3. Embedded in Text
```
Check out this paper: 10.1038/s41591-025-04133-4
```

## DOI Format

DOIs follow the pattern: `10.PREFIX/SUFFIX`
- **10**: DOI namespace
- **PREFIX**: Organization/publisher identifier
- **SUFFIX**: Unique item identifier

### Common Prefixes
- `10.1038/*` - Nature journals
- `10.1126/*` - Science journals
- `10.1371/*` - PLOS journals
- `10.1001/*` - JAMA journals
- `10.1093/*` - Oxford Academic
- `10.1016/*` - Elsevier journals

### Special Cases

**arXiv DOIs** (handled separately):
- `10.48550/arXiv.*` → Processed as arXiv preprint

**bioRxiv DOIs** (handled separately):
- `10.1101/*` → Processed as bioRxiv preprint

## Metadata Source

**API**: CrossRef REST API (`https://api.crossref.org/works/{DOI}`)

### What CrossRef Provides

Complete bibliographic metadata:
- **Title**: Full article title
- **Authors**: All authors with first/last names
- **Journal**: Publication title
- **Volume, Issue, Pages**: Complete citation details
- **Date**: Publication date(s)
- **Abstract**: Full abstract (cleaned of HTML/XML)
- **DOI**: Official DOI
- **URL**: Canonical DOI URL
- **Type**: Article type (journal-article, book-chapter, etc.)
- **Publisher**: Publisher name
- **ISSN**: Journal ISSN(s)
- **References**: Citations (if available)

## How It Works

### 1. Detection
```python
# Detects DOI patterns in URLs or text
Pattern: 10\.\d{4,}(?:\.\d+)*(?:/|%2F)[^\s]+
```

### 2. API Query
```python
url = f"https://api.crossref.org/works/{doi}"
response = requests.get(url, timeout=30.0)
```

### 3. Metadata Parsing
- Extracts all fields from JSON response
- Formats authors (firstName, lastName)
- Cleans abstract (removes HTML/XML tags)
- Handles date variations

### 4. Zotero Item Creation
- Item type: **Journal Article**
- All fields populated
- Tags: `discord-zotero-bot`, channel name
- Duplicate check by DOI/URL/title

## Example Usage

### Post in Discord
```
https://doi.org/10.1038/s41591-025-04133-4
```

### Bot Actions
1. Detects DOI: `10.1038/s41591-025-04133-4`
2. Queries CrossRef API
3. Fetches complete metadata
4. Creates journal article in Zotero

### Result in Zotero
```
Type: Journal Article
Title: A multimodal sleep foundation model for disease prediction
Authors: Thapa, Rahul; Kjaer, Magnus Ruud; He, Bryan; et al.
Publication: Nature Medicine
DOI: 10.1038/s41591-025-04133-4
Date: 2026-01-06
Volume: (as available)
Issue: (as available)
Pages: (as available)
Abstract: Sleep is a fundamental biological process with broad implications...
URL: https://doi.org/10.1038/s41591-025-04133-4
Tags: discord-zotero-bot, [channel-name]
```

## Supported Publishers

CrossRef covers most major publishers:
- ✅ Nature Publishing Group
- ✅ Science (AAAS)
- ✅ Elsevier
- ✅ Springer
- ✅ Wiley
- ✅ Taylor & Francis
- ✅ PLOS
- ✅ Oxford University Press
- ✅ Cambridge University Press
- ✅ JAMA Network
- ✅ BMJ
- ✅ And thousands more...

## Duplicate Detection

Checks for duplicates using:
1. **DOI match** (primary) - normalized, case-insensitive
2. **URL match** - checks DOI URLs
3. **Title match** (fallback)

### Example
```
First: https://doi.org/10.1038/s41591-025-04133-4
  → 🤖 Added

Second: 10.1038/s41591-025-04133-4 (bare DOI)
  → ✅ Duplicate detected
```

## Abstract Cleaning

CrossRef often returns abstracts with HTML/XML markup:
```xml
<jats:title>Abstract</jats:title><jats:p>Content here...</jats:p>
```

The bot automatically:
1. Removes `<jats:title>` tags and content
2. Strips all HTML/XML tags
3. Cleans whitespace
4. Returns clean text

**Before**:
```
<jats:title>Abstract</jats:title><jats:p>Sleep is a fundamental...</jats:p>
```

**After**:
```
Sleep is a fundamental biological process with broad implications...
```

## Error Handling

### DOI Not Found
```
Status: 404
Action: Logs warning, no item created
Message: "Could not fetch metadata for DOI"
```

### Invalid DOI Format
```
Action: Not detected as DOI
Falls back to: Generic URL processing
```

### Network Issues
```
Timeout: 30 seconds
Action: Logs error, no item created
Retry: User can post again
```

### Rate Limiting
```
CrossRef limit: Generous (typically 50 req/sec)
Bot behavior: Sequential processing prevents issues
```

## Comparison with Other Sources

| Feature | CrossRef (DOI) | arXiv | bioRxiv | PubMed |
|---------|----------------|-------|---------|---------|
| **Coverage** | Published articles | Preprints | Biology preprints | Biomedical |
| **Abstract** | Yes | Yes | Yes | Limited |
| **PDF** | Link only | Yes | Link only | Link only |
| **Citations** | Often | No | No | Limited |
| **Real-time** | Yes | Yes | Yes | Yes |
| **Item Type** | Journal Article | Preprint | Preprint | Journal Article |

## Troubleshooting

### Issue: DOI Not Detected

**Symptoms**: Generic URL processing instead of DOI

**Causes**:
- DOI format not recognized
- Special DOI (arXiv, bioRxiv) - handled separately
- Malformed DOI

**Check**:
```python
# Valid DOI patterns
✓ 10.1038/s41591-025-04133-4
✓ 10.1371/journal.pone.0123456
✗ doi:10.1038/... (may not work)
✗ DOI:10.1038/... (may not work)
```

### Issue: Metadata Incomplete

**Symptoms**: Some fields missing in Zotero

**Causes**:
- Publisher didn't provide all metadata to CrossRef
- Older publications
- Preprints (use preprint servers instead)

**Solution**: This is a data quality issue, not a bot issue

### Issue: Abstract Has HTML Tags

**Symptoms**: Tags visible in Zotero abstract

**Cause**: Bug in cleaning function (should not happen)

**Solution**: Report issue with specific DOI

### Issue: Wrong Item Type

**Symptoms**: Book chapter added as article, etc.

**Cause**: Bot currently only creates journal articles for DOIs

**Future**: Could expand to handle more types

## Advanced Features

### Content Negotiation

CrossRef supports content negotiation for different formats:
- JSON (used by bot)
- BibTeX
- RIS
- Citeproc JSON

Bot uses JSON for maximum flexibility.

### Metadata Quality

CrossRef metadata quality varies by publisher:
- **Excellent**: Nature, Science, PLOS (complete metadata)
- **Good**: Most major publishers
- **Variable**: Smaller publishers, older content

### ORCID Integration

Some CrossRef records include author ORCID IDs:
- Currently not extracted by bot
- Could be added in future versions

## Best Practices

### For Users

1. **Use DOI when available** - Most reliable identifier
2. **Check duplicate detection** - ✅ means already in library
3. **Verify metadata** - Check Zotero after addition
4. **Report issues** - Share DOIs that don't work

### For Developers

1. **Always clean abstracts** - Remove HTML/XML
2. **Normalize DOIs** - Lowercase, trim whitespace
3. **Handle errors gracefully** - Log, don't crash
4. **Respect rate limits** - Sequential processing
5. **Check duplicates** - Before adding

## Configuration

### Environment Variables
```bash
# None specific to DOI processing
# Uses general Zotero config
```

### Timeouts
```python
# CrossRef API timeout
timeout = 30.0  # seconds
```

### Rate Limiting
```python
# No explicit rate limiting
# CrossRef is generous with free tier
# Sequential processing prevents issues
```

## Statistics & Monitoring

The bot logs:
- ✅ DOI detected
- ✅ Metadata fetched successfully
- ⚠️ Metadata fetch failed
- ⚠️ Invalid DOI format
- ❌ Network errors

### Example Logs
```
INFO - Detected DOI link: 10.1038/s41591-025-04133-4
INFO - No duplicate found, fetching metadata for DOI
INFO - Added item with DOI and metadata: 10.1038/s41591-025-04133-4
```

## Future Enhancements

Potential improvements:
1. **More item types** - Books, chapters, datasets
2. **ORCID extraction** - Author identifiers
3. **Reference extraction** - Link to cited papers
4. **Altmetrics** - Social media mentions
5. **Full-text links** - Publisher PDFs
6. **Version tracking** - Multiple DOIs for same work

## Related Documentation

- [arXiv Support](arxiv_troubleshooting.md) - arXiv preprints
- [bioRxiv Support](biorxiv_support.md) - bioRxiv preprints
- [PubMed Support](pubmed_support.md) - PubMed integration
- [Duplicate Detection](../duplicate_detection.md) - How duplicates are prevented

## External Resources

- [CrossRef API Documentation](https://api.crossref.org/)
- [DOI Handbook](https://www.doi.org/the-identifier/resources/handbook)
- [CrossRef Metadata Schema](https://github.com/CrossRef/rest-api-doc)
- [Pyzotero Documentation](https://pyzotero.readthedocs.io/)

## Summary

✅ **Comprehensive metadata** from CrossRef  
✅ **Clean abstracts** with HTML/XML removed  
✅ **Duplicate detection** by DOI  
✅ **Wide publisher coverage** via CrossRef  
✅ **Automatic tagging** with bot + channel tags  
✅ **Error handling** for network issues  
✅ **Fast processing** with 30s timeout  
✅ **Journal article** item type in Zotero  

DOI/CrossRef support provides the most complete metadata for published scholarly articles! 📚
