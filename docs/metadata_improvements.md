# Metadata Improvements

## Problem
The initial implementation was adding articles to Zotero but with minimal or missing metadata. Items were created as basic placeholders without proper bibliographic information.

## Solution
Integrated external metadata APIs to fetch complete bibliographic data for each paper type.

## Changes Made

### 1. New Dependencies
Added `httpx>=0.28.1` for async HTTP requests to external APIs.

### 2. New Metadata Fetching Functions

#### `fetch_crossref_metadata(doi: str)`
- Connects to CrossRef API
- Retrieves complete bibliographic data for DOIs
- Returns: title, authors, journal, volume, issue, pages, date, abstract, URL

#### `fetch_arxiv_metadata(arxiv_id: str)`
- Connects to arXiv API
- Parses XML response
- Returns: title, authors, abstract, published date, categories, DOI (if available), URL

#### `fetch_pubmed_metadata(pmid: str)`
- Connects to NCBI PubMed E-utilities API
- Retrieves article summaries
- Returns: title, authors, journal, volume, issue, pages, date, DOI (if available), URL

#### `fetch_webpage_metadata(url: str)`
- Scrapes HTML meta tags from scholarly websites
- Extracts citation metadata (Dublin Core, HighWire Press, etc.)
- Returns: title, authors, journal, DOI, publication date
- Special handling: If DOI found, redirects to CrossRef for complete metadata

### 3. Enhanced Zotero Integration

#### Updated `add_to_zotero_by_identifier()`
**Before**: Created minimal journal article template with just the identifier

**After**: 
- Fetches full metadata from appropriate API
- Populates complete Zotero item template
- Properly formats authors (first/last name)
- Adds all available bibliographic fields
- Uses correct item types (journalArticle for DOI/PubMed, preprint for arXiv)

#### Updated `add_to_zotero_by_url()`
**Before**: Created webpage item with just URL and generic title

**After**:
- Attempts to extract metadata from HTML
- Looks for DOI in meta tags and uses CrossRef if found
- Creates appropriate item type (journalArticle vs webpage)
- Populates author, journal, date fields when available
- Provides meaningful titles from page metadata

## Metadata Quality by Source

### DOI (via CrossRef)
✅ **Highest Quality**
- Complete bibliographic data
- Standardized format
- Includes abstracts
- Author names properly parsed

**Example Result in Zotero**:
```
Type: Journal Article
Title: A multimodal sleep foundation model for disease prediction
Authors: Thapa, Rahul; Kjaer, Magnus Ruud; He, Bryan; et al.
Publication: Nature Medicine
DOI: 10.1038/s41591-025-04133-4
Date: 2026-01-06
Volume/Issue/Pages: (as available)
Abstract: (full abstract)
URL: https://doi.org/10.1038/s41591-025-04133-4
```

### arXiv (via arXiv API)
✅ **High Quality**
- Complete preprint metadata
- Full abstracts
- Categories/subjects
- Version tracking

**Example Result in Zotero**:
```
Type: Preprint
Title: (paper title)
Authors: (full author list)
Repository: arXiv
Archive ID: 2401.12345
Date: (submission date)
Abstract: (full abstract)
Categories: (cs.AI, etc.)
URL: https://arxiv.org/abs/2401.12345
```

### PubMed (via NCBI API)
✅ **High Quality**
- Complete article metadata
- Links to DOI when available
- Journal information
- Publication details

**Example Result in Zotero**:
```
Type: Journal Article
Title: (paper title)
Authors: (full author list)
Publication: (journal name)
Volume/Issue/Pages: (complete)
Date: (publication date)
DOI: (if available)
URL: https://pubmed.ncbi.nlm.nih.gov/12345678/
```

### Generic URLs (via HTML scraping)
⚠️ **Variable Quality** (depends on source)
- Extracts citation meta tags
- Quality depends on publisher's metadata
- If DOI found → redirects to CrossRef (high quality)
- Otherwise → basic webpage item

**Example Result for Nature.com**:
1. Bot detects URL: `https://www.nature.com/articles/s41591-025-04133-4`
2. Scrapes HTML, finds DOI in meta tags: `10.1038/s41591-025-04133-4`
3. Fetches complete metadata from CrossRef
4. Creates full journal article with all fields

## Testing the Improvements

### Test with DOI
Post in papers channel:
```
https://doi.org/10.1038/s41591-025-04133-4
```

**Expected in Zotero**:
- Complete journal article
- All authors properly formatted
- Full abstract
- Publication details

### Test with Nature URL
Post in papers channel:
```
https://www.nature.com/articles/s41591-025-04133-4
```

**Expected**:
- Bot extracts DOI from page
- Uses CrossRef metadata
- Same result as direct DOI link

### Test with arXiv
Post in papers channel:
```
https://arxiv.org/abs/2401.12345
```

**Expected in Zotero**:
- Preprint item type
- Full abstract
- All authors
- Categories listed

### Test with PubMed
Post in papers channel:
```
https://pubmed.ncbi.nlm.nih.gov/12345678/
```

**Expected in Zotero**:
- Complete journal article
- Journal name
- Volume/issue/pages
- DOI if available

## Error Handling

The implementation includes robust error handling:
- Network timeouts (30 seconds)
- API failures fall back gracefully
- Logs warnings when metadata unavailable
- Still creates basic item if metadata fetch fails
- Continues processing other links on error

## Performance Considerations

- Metadata fetching adds ~1-2 seconds per link (API calls)
- Async implementation prevents blocking
- Timeouts prevent indefinite hangs
- Rate limiting respected (0.1s delay between messages in scan)

## Benefits

1. ✅ **Complete Citations**: All papers now have proper bibliographic data
2. ✅ **Better Organization**: Correct item types (journal article, preprint, etc.)
3. ✅ **Searchable**: Full text in abstracts makes papers easier to find
4. ✅ **Export Ready**: Complete metadata for bibliography generation
5. ✅ **Professional**: Library looks polished and well-maintained
