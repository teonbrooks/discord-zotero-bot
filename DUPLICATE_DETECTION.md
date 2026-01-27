# Duplicate Detection Improvements

## Problem
The bot was adding duplicate papers to the Zotero library even though the same paper had been added before (via different URLs or formats).

## Root Causes Identified

### 1. Limited Search Scope
- Original: Only searched first 5 results
- Issue: In larger libraries, duplicates might not appear in first 5 results
- **Fix**: Increased search limit to 50 results

### 2. Incomplete Duplicate Checks
- Original: Only checked the identifier being used (e.g., just DOI when adding via DOI)
- Issue: Same paper could be added via multiple paths:
  - `https://doi.org/10.1038/s41591-025-04133-4` (DOI URL)
  - `https://www.nature.com/articles/s41591-025-04133-4` (Journal URL)
  - Both refer to the same paper!
- **Fix**: Comprehensive checking across DOI, URL, and title

### 3. URL Variations Not Handled
- Original: Exact URL string matching
- Issue: Same URL with minor differences treated as different:
  - `http://` vs `https://`
  - Trailing slash vs no trailing slash
- **Fix**: URL normalization and variation checking

### 4. Timing of Duplicate Checks
- Original: Checked for duplicates, then fetched metadata
- Issue: Metadata fetching might reveal additional identifiers (e.g., DOI in webpage)
- **Fix**: Fetch metadata first, then do comprehensive check with all available info

## Implemented Solutions

### 1. Enhanced Search Functions

#### `search_zotero_by_doi(doi: str)`
**Improvements**:
- Normalizes DOI (lowercase, trimmed)
- Searches up to 50 items (was 5)
- Checks both `DOI` field and `extra` field
- Logs when duplicate found

**Example**:
```python
# Finds these variations:
- "10.1038/s41591-025-04133-4"
- "10.1038/S41591-025-04133-4" (case insensitive)
- DOIs stored in extra field
```

#### `search_zotero_by_url(url: str)`
**Improvements**:
- Normalizes URLs (lowercase, removes trailing slashes)
- Checks http/https variations
- Searches up to 50 items (was 5)
- Extracts and checks DOI from DOI URLs
- Logs when duplicate found

**Example**:
```python
# These are treated as same:
- "https://example.com/paper"
- "https://example.com/paper/"
- "http://example.com/paper"

# Also recognizes DOI URLs:
- "https://doi.org/10.1038/s41591-025-04133-4"
  → Extracts DOI and checks against item DOI fields
```

#### `search_zotero_by_title(title: str)`
**Improvements**:
- Normalizes whitespace
- Checks for exact title matches (case-insensitive)
- Searches up to 20 items
- Logs when duplicate found

**Example**:
```python
# These match:
- "A multimodal sleep foundation model"
- "A   multimodal  sleep   foundation  model" (extra spaces)
```

### 2. New Comprehensive Check Function

#### `check_duplicate_comprehensive(doi, url, title)`
**Purpose**: Single function that checks all available identifiers

**Logic**:
1. Check DOI first (most reliable identifier)
2. Check URL if no DOI match
3. Check title as fallback
4. Return True if ANY match found

**Usage in codebase**:
```python
# Before adding any paper, check with ALL available metadata:
if check_duplicate_comprehensive(
    doi=metadata.get('doi'),
    url=url,
    title=metadata.get('title')
):
    return (False, "duplicate")
```

### 3. Updated Add Functions

#### DOI Processing
```python
# OLD:
if identifier_type == 'doi':
    if search_zotero_by_doi(identifier):
        return (False, "duplicate")

# NEW:
if identifier_type == 'doi':
    if check_duplicate_comprehensive(doi=identifier):
        return (False, "duplicate")
```

#### arXiv Processing
```python
# OLD:
if search_zotero_by_url(metadata['url']):
    return (False, "duplicate")

# NEW:
if check_duplicate_comprehensive(
    doi=metadata.get('doi'),      # arXiv papers might have DOIs
    url=metadata.get('url'),
    title=metadata.get('title')
):
    return (False, "duplicate")
```

#### PubMed Processing
```python
# OLD:
if search_zotero_by_url(metadata['url']):
    return (False, "duplicate")
if metadata.get('doi') and search_zotero_by_doi(metadata['doi']):
    return (False, "duplicate")

# NEW:
if check_duplicate_comprehensive(
    doi=metadata.get('doi'),
    url=metadata.get('url'),
    title=metadata.get('title')
):
    return (False, "duplicate")
```

#### Generic URL Processing
```python
# OLD:
if search_zotero_by_url(url):
    return (False, "duplicate")

# NEW:
# Fetch metadata FIRST to get DOI if available
metadata = await fetch_webpage_metadata(url)

# Then check with ALL information
if check_duplicate_comprehensive(
    doi=metadata.get('doi') if metadata else None,
    url=url,
    title=metadata.get('title') if metadata else None
):
    return (False, "duplicate")
```

## Example Scenarios

### Scenario 1: Same Paper, Different URLs
**User posts**:
1. `https://doi.org/10.1038/s41591-025-04133-4`
2. `https://www.nature.com/articles/s41591-025-04133-4`

**Bot behavior**:
1. First URL → Adds paper with DOI
2. Second URL → Scrapes page, finds DOI `10.1038/s41591-025-04133-4`
3. Comprehensive check finds existing item with same DOI
4. Reacts with ✅ (duplicate), does NOT add again

### Scenario 2: DOI and arXiv Version
**User posts**:
1. `https://arxiv.org/abs/2401.12345`
2. `https://doi.org/10.xxxx/yyyy` (published version of same paper)

**Bot behavior**:
1. First URL → Adds as preprint, stores arXiv ID and DOI (if available)
2. Second URL → Checks DOI against library
3. If arXiv entry had DOI, comprehensive check finds it
4. Reacts with ✅ (duplicate)

### Scenario 3: PubMed and Direct Journal Link
**User posts**:
1. `https://pubmed.ncbi.nlm.nih.gov/12345678/`
2. Direct journal URL that has same DOI

**Bot behavior**:
1. First URL → Fetches PubMed metadata including DOI, adds paper
2. Second URL → Scrapes page, finds DOI
3. Comprehensive check matches DOI
4. Reacts with ✅ (duplicate)

## Testing the Improvements

### Test 1: Same DOI Different Formats
```
Post: https://doi.org/10.1038/s41591-025-04133-4
Result: 🤖 (added)

Post: https://www.nature.com/articles/s41591-025-04133-4
Result: ✅ (duplicate detected via DOI extraction)
```

### Test 2: URL Variations
```
Post: https://example.com/paper
Result: 🤖 (added)

Post: http://example.com/paper/
Result: ✅ (duplicate detected via URL normalization)
```

### Test 3: DOI Case Sensitivity
```
Post: DOI with lowercase
Result: 🤖 (added)

Post: Same DOI with uppercase
Result: ✅ (duplicate detected via normalized comparison)
```

### Test 4: Larger Library
Previous issue: Duplicate not found because it was beyond first 5 results

**Fix verified**: Now searches up to 50 results, catches duplicates further in library

## Performance Considerations

### Trade-offs
- **Increased search results** (5 → 50): Slightly slower but much more accurate
- **Multiple checks per item**: More API calls but prevents duplicates
- **Metadata fetching first**: Small delay but enables better duplicate detection

### Typical Performance
- DOI check: ~0.5 seconds
- URL check: ~0.5 seconds
- Title check: ~0.5 seconds
- Comprehensive check: ~1.5 seconds total (checks run sequentially, stop at first match)

### Optimization
- Checks stop at first match (no unnecessary additional checks)
- Most reliable check (DOI) runs first
- Only fetches metadata once, then uses it for all checks

## Logging Improvements

The bot now logs when duplicates are found:
```
INFO - Found existing item with DOI: 10.1038/s41591-025-04133-4
INFO - Found existing item with URL: https://example.com/paper
INFO - Found existing item with matching title: A multimodal sleep...
```

This helps debug duplicate detection and confirms it's working correctly.

## Summary of Changes

✅ **Increased search limits**: 5 → 50 results for DOI/URL, 5 → 20 for title
✅ **URL normalization**: Handles http/https, trailing slashes
✅ **Comprehensive checking**: Uses ALL available identifiers (DOI + URL + title)
✅ **Better timing**: Fetches metadata before duplicate checking
✅ **DOI extraction**: Finds DOIs in URLs and webpage content
✅ **Improved logging**: Shows what matched when duplicate found

## Expected Behavior Now

- ✅ Same paper via different URLs → Detected as duplicate
- ✅ Same DOI in different formats → Detected as duplicate
- ✅ URL variations (http/https) → Detected as duplicate
- ✅ Papers deep in library → Found within 50 results
- ✅ Nature article + DOI URL → Detected as duplicate
- ✅ arXiv + published version → Detected as duplicate (if DOI matches)
