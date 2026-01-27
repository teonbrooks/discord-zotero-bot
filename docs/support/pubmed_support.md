# PubMed Support

## Overview

The bot supports PubMed links, fetching metadata from the NCBI PubMed E-utilities API. PubMed is a database of biomedical and life sciences literature maintained by the National Library of Medicine.

## Supported Formats

### 1. PubMed URLs
```
https://pubmed.ncbi.nlm.nih.gov/12345678/
https://www.ncbi.nlm.nih.gov/pubmed/12345678
```

### 2. PMID Format
```
PMID: 12345678
PMID:12345678
PMID 12345678
```

### 3. Bare PMID
```
12345678 (in context as a PubMed ID)
```

## PMID Format

**PMID** = PubMed ID (or PubMed Unique Identifier)
- Unique integer identifier
- Assigned sequentially
- 8-9 digits typically
- Example: `38180801`

## Metadata Source

**API**: NCBI E-utilities ESummary API

**Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`

### What PubMed Provides

- **Title**: Article title
- **Authors**: Author names (Last, First Middle format)
- **Journal**: Full journal name
- **Date**: Publication date
- **Volume**: Journal volume
- **Issue**: Journal issue
- **Pages**: Page range
- **DOI**: Associated DOI (if available)
- **PMID**: PubMed ID
- **Abstract**: Limited (not always available in ESummary)

### What PubMed Doesn't Provide

- ❌ Full abstracts (via ESummary)
- ❌ Full text
- ❌ PDF links
- ❌ Citations/references

**Note**: For complete abstracts, would need EFetch API (not currently implemented).

## How It Works

### 1. Detection
```python
# Patterns for PubMed ID extraction
- pubmed\.ncbi\.nlm\.nih\.gov/(\d+)
- ncbi\.nlm\.nih\.gov/pubmed/(\d+)
- PMID:?\s*(\d+)
```

### 2. API Query
```python
url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
params = {
    'db': 'pubmed',
    'id': pmid,
    'retmode': 'json'
}
```

### 3. Metadata Parsing
- Extracts fields from JSON response
- Formats author names
- Handles date variations
- Extracts DOI from articleids array

### 4. Zotero Item Creation
- Item type: **Journal Article**
- All available fields populated
- Tags: `discord-zotero-bot`, channel name
- Duplicate check by DOI (if available), URL, or title

## Example Usage

### Post in Discord
```
https://pubmed.ncbi.nlm.nih.gov/38180801/
```

### Bot Actions
1. Detects PMID: `38180801`
2. Queries PubMed ESummary API
3. Fetches metadata
4. Checks for DOI (if available)
5. Creates journal article in Zotero

### Result in Zotero
```
Type: Journal Article
Title: [Article title]
Authors: [Last, First Middle; ...]
Publication: [Full journal name]
Volume: [volume]
Issue: [issue]
Pages: [pages]
Date: [publication date]
DOI: [DOI if available]
URL: https://pubmed.ncbi.nlm.nih.gov/38180801/
Tags: discord-zotero-bot, [channel-name]
```

## PubMed Coverage

### Databases Covered
- **MEDLINE**: Biomedical journals
- **PubMed Central**: Open access full text
- **NCBI Bookshelf**: Book chapters
- **PMC**: PubMed Central articles

### Subject Areas
- Medicine
- Nursing
- Dentistry
- Veterinary Medicine
- Health Care Systems
- Preclinical Sciences

### Date Range
- 1946-present (MEDLINE)
- Older citations also available
- 40+ million citations

## Duplicate Detection

Checks for duplicates using:
1. **DOI match** (if PubMed provides DOI)
2. **URL match** (PubMed URL)
3. **Title match** (fallback)

### Example
```
First: https://pubmed.ncbi.nlm.nih.gov/38180801/
  → 🤖 Added

Second: PMID: 38180801
  → ✅ Duplicate detected
```

## Author Name Handling

PubMed provides authors in "Last FM" format:
```
Smith J
Doe JA
Johnson-Brown MK
```

Bot parses to:
```
lastName: "Smith"
firstName: "J"

lastName: "Doe"
firstName: "JA"

lastName: "Johnson-Brown"
firstName: "MK"
```

## DOI Integration

### When PubMed Has DOI
If PubMed metadata includes a DOI:
1. DOI is stored in item
2. Enables cross-linking
3. Improves duplicate detection

### When to Use DOI Instead
If you have a DOI, **prefer the DOI URL**:
- ✅ Better: `https://doi.org/10.xxxx/yyyy`
- ⚠️ OK: `https://pubmed.ncbi.nlm.nih.gov/xxxxx/`

DOI provides:
- More complete metadata (via CrossRef)
- Full abstracts
- Better standardization

## Error Handling

### PMID Not Found
```
Status: API returns error
Action: Logs warning, no item created
Message: "Could not fetch metadata for PubMed"
```

### Invalid PMID
```
Action: Not detected as PubMed
Falls back to: Generic URL processing
```

### Network Issues
```
Timeout: 30 seconds
Action: Logs error, no item created
Retry: User can post again
```

### API Rate Limits
```
NCBI limit: 3 requests/second (no API key)
NCBI limit: 10 requests/second (with API key)
Bot behavior: Sequential processing, no API key
```

**Note**: For high-volume usage, consider adding NCBI API key.

## Comparison with Other Sources

| Feature | PubMed | DOI/CrossRef | arXiv | bioRxiv |
|---------|--------|--------------|-------|---------|
| **Coverage** | Biomedical | All disciplines | Preprints | Biology preprints |
| **Abstract** | Limited | Full | Full | Full |
| **DOI Link** | Sometimes | Always | Sometimes | Always |
| **Author Detail** | Basic | Complete | Complete | Complete |
| **Free Access** | Yes | Yes | Yes | Yes |
| **Item Type** | Journal Article | Journal Article | Preprint | Preprint |

## Limitations

### 1. Limited Abstracts
ESummary API doesn't return full abstracts.

**Workaround**: If DOI is available, bot uses it for CrossRef metadata.

### 2. Author Names
Format is "Last FM" without full first names.

**Impact**: Less detail than CrossRef provides.

### 3. No Full Text
PubMed links to abstracts, not full text.

**Alternative**: PubMed Central (PMC) has full text for open access articles.

### 4. Rate Limiting
Without API key, limited to 3 req/sec.

**Solution**: For high-volume, add API key support.

## Best Practices

### For Users

1. **Use DOI if available** - Better metadata
2. **Check for PMC version** - Open access full text
3. **Verify metadata** - PubMed may have incomplete info
4. **Include PMID in notes** - For citation purposes

### For Developers

1. **Prefer DOI** - When PubMed provides DOI
2. **Handle missing data** - Not all fields always present
3. **Parse author names** - "Last FM" format
4. **Consider API key** - For higher rate limits
5. **Future: Use EFetch** - For complete abstracts

## Advanced Features

### PubMed Central (PMC)

Some PubMed articles have PMC versions:
- Open access
- Full text available
- PDFs available

**Future enhancement**: Detect PMC links separately.

### MeSH Terms

PubMed includes MeSH (Medical Subject Headings):
- Controlled vocabulary
- Improves searching
- Not currently extracted

**Future enhancement**: Add MeSH terms as Zotero tags.

### Publication Types

PubMed categorizes by type:
- Journal Article
- Review
- Clinical Trial
- Meta-Analysis
- etc.

**Future enhancement**: Map to Zotero item types.

## Troubleshooting

### Issue: PMID Not Detected

**Symptoms**: Processed as generic URL

**Causes**:
- PMID format not recognized
- URL format different
- Non-PubMed link

**Check**:
```python
# Valid formats
✓ https://pubmed.ncbi.nlm.nih.gov/12345678/
✓ PMID: 12345678
✓ PMID:12345678
✗ pm:12345678 (not recognized)
✗ pubmed 12345678 (may not work)
```

### Issue: Incomplete Metadata

**Symptoms**: Missing fields in Zotero

**Causes**:
- PubMed record incomplete
- Older citations
- In-process citations

**Solution**: 
- Check PubMed website
- Use DOI if available
- Manually complete in Zotero

### Issue: Wrong Authors

**Symptoms**: Author names truncated or wrong

**Cause**: "Last FM" format limitations

**Solution**: 
- Use DOI for better author data
- Manually edit in Zotero

## Configuration

### Environment Variables
```bash
# None specific to PubMed
# Could add:
NCBI_API_KEY=your_key_here  # For higher rate limits
```

### Timeouts
```python
# PubMed API timeout
timeout = 30.0  # seconds
```

### Rate Limiting
```python
# Current: None (3 req/sec limit applies)
# Future: Add API key support for 10 req/sec
```

## Statistics & Monitoring

The bot logs:
- ✅ PMID detected
- ✅ Metadata fetched successfully
- ⚠️ Metadata fetch failed
- ⚠️ Invalid PMID
- ❌ Network errors

### Example Logs
```
INFO - Detected PubMed link with ID: 38180801
INFO - Processing PubMed paper with ID: 38180801
INFO - Successfully fetched PubMed metadata for: 38180801
INFO - Added PubMed item with metadata: 38180801
```

## Future Enhancements

Potential improvements:
1. **EFetch API** - Get complete abstracts
2. **PMC detection** - Separate handling for PMC links
3. **MeSH terms** - Add as Zotero tags
4. **API key support** - Higher rate limits
5. **Full-text links** - Add PMC PDF links
6. **Publication types** - Better item type mapping
7. **Related articles** - Link to similar papers

## Related Documentation

- [DOI/CrossRef Support](doi_crossref_support.md) - For DOI-based metadata
- [bioRxiv Support](biorxiv_support.md) - Biology preprints
- [arXiv Support](arxiv_troubleshooting.md) - Physics/CS preprints
- [Duplicate Detection](../duplicate_detection.md) - How duplicates are prevented

## External Resources

- [PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/)
- [E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [NCBI API Keys](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)
- [MeSH Database](https://www.ncbi.nlm.nih.gov/mesh/)

## Summary

✅ **Biomedical focus** via PubMed  
✅ **40+ million citations** available  
⚠️ **Limited abstracts** (ESummary limitation)  
✅ **DOI integration** when available  
✅ **Automatic tagging** with bot + channel tags  
✅ **Duplicate detection** by DOI/URL/title  
✅ **Fast processing** with 30s timeout  
✅ **Journal article** item type in Zotero  

PubMed support provides access to the world's largest biomedical literature database! 🏥
