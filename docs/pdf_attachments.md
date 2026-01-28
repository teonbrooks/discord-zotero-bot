# PDF Attachment Feature

## Overview

The bot automatically downloads and attaches PDFs to Zotero items when papers are added. This feature works for sources that provide free, open access to PDFs.

Additionally, you can use the `/attach_pdfs` command to scan your existing Zotero library and attach PDFs to items that don't have them yet.

## Supported Sources

### ✅ arXiv (Always Available)
**Coverage**: 100% of papers  
**How it works**: arXiv provides free PDF access for all preprints

```
Example: https://arxiv.org/abs/2404.05553
PDF URL: https://arxiv.org/pdf/2404.05553.pdf
Result: PDF automatically downloaded and attached
```

### ✅ bioRxiv (Always Available)
**Coverage**: 100% of papers  
**How it works**: bioRxiv provides free PDF access for all preprints

```
Example: https://doi.org/10.1101/2023.05.15.540123
PDF URL: https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1.full.pdf
Result: PDF automatically downloaded and attached
```

### ⚠️ DOI/CrossRef (When Available)
**Coverage**: Variable (depends on publisher and open access status)  
**How it works**: Checks CrossRef metadata for open access PDF links

```
Example: Open access paper with PDF link
Result: PDF downloaded and attached

Example: Paywalled paper
Result: Metadata added, no PDF attached
```

### ❌ PubMed (Not Yet Implemented)
**Coverage**: Could be added via PubMed Central (PMC)  
**Status**: Planned for future enhancement  
**Workaround**: If paper has a DOI, the DOI link may provide PDF

### ❌ Generic URLs (No PDF Attachment)
**Coverage**: N/A  
**How it works**: Generic URL scraping doesn't attempt PDF download

## How It Works

### 1. Paper Added
When a paper is successfully added to Zotero, the bot checks if PDF attachment is available for that source type.

### 2. PDF URL Determined
```python
# arXiv: Direct formula-based URL
https://arxiv.org/pdf/{arxiv_id}.pdf

# bioRxiv: DOI-based URL with version
https://www.biorxiv.org/content/{doi}{version}.full.pdf

# DOI: Check CrossRef metadata for PDF links
Looks for links with content-type: application/pdf
```

### 3. PDF Downloaded
- HTTP request with 60-second timeout
- Follows redirects automatically
- Verifies content is actually a PDF (checks for `%PDF` header)
- Maximum size: No limit (downloads entire file)

### 4. PDF Attached
- Saves to temporary file
- Uploads to Zotero via API
- Cleans up temporary file
- Attachment appears in Zotero immediately

## Behavior & Logging

### Successful Attachment
```
INFO - Added arXiv item with metadata: 2404.05553
INFO - Attaching arXiv PDF from: https://arxiv.org/pdf/2404.05553.pdf
INFO - Attempting to download PDF from: https://arxiv.org/pdf/2404.05553.pdf
INFO - Successfully downloaded PDF (1234567 bytes)
INFO - Successfully attached PDF to Zotero item ABCD1234
```

### No PDF Available
```
INFO - Added item with DOI and metadata: 10.1038/s41591-025-04133-4
INFO - No open access PDF available for DOI: 10.1038/s41591-025-04133-4
```

### Download Failed
```
INFO - Attempting to download PDF from: https://example.com/paper.pdf
WARNING - Failed to download PDF: HTTP 404
```

### Invalid PDF Content
```
INFO - Successfully downloaded PDF (12345 bytes)
WARNING - Downloaded content doesn't appear to be a PDF
```

## Error Handling

### Timeouts
- **Duration**: 60 seconds for PDF download
- **Behavior**: Logs warning, paper is added without PDF
- **Retry**: No automatic retry (user can manually attach later)

### HTTP Errors
- **404 Not Found**: Logs warning, continues without PDF
- **403 Forbidden**: Logs warning, continues without PDF
- **500 Server Error**: Logs warning, continues without PDF
- **Other errors**: Logs error with details

### Invalid Content
- **Not a PDF**: Checks for PDF magic number (`%PDF`)
- **HTML page**: Common for paywall redirects, detected and skipped
- **Empty file**: Logs warning, continues without PDF

### Zotero API Errors
- **Upload failed**: Logs error, paper metadata already saved
- **Permission error**: Logs error, check Zotero API token permissions
- **Quota exceeded**: May fail if Zotero storage quota exceeded

## Limitations

### 1. Open Access Only
The bot **only** downloads PDFs that are freely and legally available. It:
- ✅ Downloads from arXiv (always open)
- ✅ Downloads from bioRxiv (always open)
- ✅ Downloads from CrossRef if PDF link provided
- ❌ Does **not** bypass paywalls
- ❌ Does **not** use Sci-Hub or similar services
- ❌ Does **not** attempt institutional access

### 2. File Size
- No size limit enforced
- Large files (100+ MB) will take longer
- Very large files may timeout (60s limit)
- Network speed dependent

### 3. Network Requirements
- Requires stable internet connection
- Downloads are sequential (one at a time)
- `/scan_papers` command will be slower with PDF downloads
- Consider running backfill scans during off-hours

### 4. Zotero Storage
- PDFs count against Zotero storage quota
- Free plan: 300 MB
- Paid plans: Up to unlimited
- Check storage at: https://www.zotero.org/settings/storage

## Configuration

### Environment Variables
No additional environment variables needed. PDF attachment is enabled by default.

### Disabling PDF Attachments
To disable PDF attachments, you would need to comment out the PDF attachment code blocks in `zotero-bot.py`:

```python
# Comment out these sections in add_to_zotero_by_identifier():
# if items and 'successful' in items and items['successful']:
#     item_key = items['successful']['0']['key']
#     pdf_url = get_pdf_url('arxiv', identifier, metadata)
#     if pdf_url:
#         await download_and_attach_pdf(item_key, pdf_url, f"arxiv_{identifier}.pdf")
```

**Note**: A configuration option for this may be added in future versions.

## Performance Impact

### Single Paper
- **Without PDF**: ~1-2 seconds total
- **With PDF (arXiv)**: ~3-5 seconds total (adds 1-3s for download)
- **With PDF (bioRxiv)**: ~4-6 seconds total (adds 2-4s for download)

### Batch Processing (`/scan_papers`)
- **10 papers without PDFs**: ~10-20 seconds
- **10 papers with PDFs**: ~30-60 seconds
- **100 papers with PDFs**: ~5-10 minutes

**Recommendation**: For large backfills, consider running during off-hours.

## Troubleshooting

### Issue: No PDFs Being Attached

**Symptoms**: Papers added but no PDFs in Zotero

**Possible Causes**:
1. Source doesn't provide open access PDFs (e.g., paywalled DOIs)
2. Network issues preventing downloads
3. Zotero storage quota exceeded

**Check**:
```bash
# View bot logs for PDF download attempts
grep "PDF" bot_logs.txt

# Look for:
# - "Attaching PDF from:" (attempt made)
# - "Successfully attached PDF" (success)
# - "No open access PDF" (not available)
# - "Failed to download PDF" (error)
```

### Issue: PDF Download Timeouts

**Symptoms**: "Timeout while downloading PDF" in logs

**Causes**:
- Slow network connection
- Large PDF files
- Server slow to respond

**Solutions**:
- Check network connection
- Large files (>50MB) may timeout - manual download may be needed
- Wait and try again later

### Issue: "Downloaded content doesn't appear to be a PDF"

**Symptoms**: Download succeeds but attachment fails

**Causes**:
- Server returned HTML error page instead of PDF
- Redirect to paywall login page
- Corrupted download

**Solutions**:
- Usually indicates PDF is not freely available
- Check URL manually in browser
- Paper metadata is still saved

### Issue: Zotero Storage Quota Exceeded

**Symptoms**: "Error attaching PDF to Zotero" in logs

**Causes**:
- Free Zotero account (300 MB) is full
- Need to upgrade or clean up storage

**Solutions**:
1. Check storage: https://www.zotero.org/settings/storage
2. Delete old PDFs from Zotero
3. Upgrade to paid plan
4. Use file syncing instead of Zotero storage

## Backfilling PDFs for Existing Items

### `/attach_pdfs` Command

Use this command to scan your existing Zotero library and attach PDFs to items that don't have them.

**Syntax**:
```
/attach_pdfs [limit]
```

**Parameters**:
- `limit`: Maximum items to process (default: 50, max: 200)

**What it does**:
1. Fetches items from your Zotero library
2. Checks each item for existing PDF attachments
3. Skips items that already have PDFs
4. Extracts identifiers (DOI, arXiv ID, bioRxiv DOI) from item metadata
5. Attempts to download and attach PDFs using the same logic as automatic attachment
6. Reports detailed statistics

**Example usage**:
```
/attach_pdfs limit:100
```

**Output example**:
```
✅ PDF Attachment Scan Complete

📊 Statistics:
• Items scanned: 100
• Already have PDFs: 45
• No identifier found: 15
• PDF not available: 10
• ✅ PDFs attached: 28
• ❌ Attachment failed: 2

🎉 Successfully attached 28 PDF(s)!
```

### Use Cases

**1. Backfill for Old Items**
Papers added before the PDF attachment feature can now get their PDFs:
```
/attach_pdfs limit:200
```

**2. Retry Failed Downloads**
If PDFs failed to download initially (network issues, timeouts), retry them:
```
/attach_pdfs limit:50
```

**3. Manually Created Items**
Items you created manually in Zotero can get PDFs:
```
/attach_pdfs limit:100
```

**4. After Upgrading Bot**
After updating the bot with PDF feature, backfill all items:
```
/attach_pdfs limit:200
```

### What Gets Scanned

The command looks for these identifiers in your Zotero items:

**DOI field**:
- Regular DOI → checks for open access PDF
- arXiv DOI (`10.48550/arXiv.*`) → downloads arXiv PDF
- bioRxiv DOI (`10.1101/*`) → downloads bioRxiv PDF

**Repository field**:
- `repository: "arXiv"` + `archiveID` → downloads from arXiv
- `repository: "bioRxiv"` + `archiveID` → downloads from bioRxiv

**URL field**:
- arXiv URLs → extracts ID and downloads
- bioRxiv URLs → extracts DOI and downloads

### Limitations

**Items Skipped**:
- Items that already have PDF attachments
- Items without identifiable identifiers (DOI, arXiv ID, etc.)
- Items from paywalled sources (no open access PDF)
- Attachments and notes (not regular items)

**Processing Limits**:
- Maximum 200 items per command run (to prevent timeouts)
- Processes items sequentially (3-6 seconds each with PDF)
- Large scans may take several minutes

**Success Rates**:
- arXiv items: ~99% success
- bioRxiv items: ~95% success  
- DOI items: ~20-30% success (depends on open access)
- Items without proper identifiers: 0% (can't determine source)

### Performance

**Timing**:
- 50 items: ~3-5 minutes (with PDFs)
- 100 items: ~6-10 minutes (with PDFs)
- 200 items: ~12-20 minutes (with PDFs)

**Recommendations**:
- Start with small limits (50-100) to test
- Run large scans during off-hours
- Monitor progress with status updates
- Can be run multiple times safely (skips items with PDFs)

## Manual PDF Attachment

If automatic attachment fails, you can manually add PDFs:

### In Zotero Desktop
1. Select the item
2. Click "Add Attachment" → "Attach Link to File" or "Attach Stored Copy of File"
3. Browse to PDF file or paste URL

### For arXiv Papers
1. Item is in Zotero without PDF
2. Manually visit: `https://arxiv.org/pdf/{arxiv_id}.pdf`
3. Download PDF
4. Drag and drop onto Zotero item

### For bioRxiv Papers
1. Visit paper page
2. Click "Download PDF" button
3. Drag and drop onto Zotero item

## Future Enhancements

### Planned Features
- [ ] PubMed Central (PMC) PDF support
- [ ] Configuration option to enable/disable PDF downloads
- [ ] Retry mechanism for failed downloads
- [ ] Progress indication for large PDFs
- [ ] Parallel PDF downloads (multiple at once)
- [ ] Size limit configuration
- [ ] medRxiv PDF support
- [ ] SSRN PDF support

### Under Consideration
- [ ] Institutional access support (via proxy)
- [ ] Unpaywall API integration for open access copies
- [ ] Google Scholar PDF link detection
- [ ] ResearchGate download support (if legally available)

## Best Practices

### For Users
1. **Monitor storage**: Check Zotero storage regularly
2. **Review attachments**: Verify PDFs attached correctly
3. **Manual fallback**: For failed downloads, add PDFs manually
4. **Batch wisely**: Large backfills are slow - be patient

### For Developers
1. **Respect robots.txt**: Current implementation respects server policies
2. **No paywalls**: Never attempt to bypass paywalls
3. **Legal only**: Only download freely available content
4. **Error handling**: Graceful failure - paper metadata always saved
5. **Logging**: Detailed logs for troubleshooting

## Statistics

### Success Rates (Typical)
- **arXiv**: ~99% (only fails on network errors)
- **bioRxiv**: ~95% (occasional server issues)
- **DOI**: ~20-30% (depends on open access prevalence)
- **PubMed**: 0% (not yet implemented)

### Storage Usage (Typical)
- **arXiv paper**: 300 KB - 2 MB
- **bioRxiv paper**: 1 MB - 5 MB  
- **Journal article**: 500 KB - 3 MB

## Related Documentation

- [arXiv Support](support/arxiv_troubleshooting.md) - arXiv-specific details
- [bioRxiv Support](support/biorxiv_support.md) - bioRxiv-specific details
- [DOI/CrossRef Support](support/doi_crossref_support.md) - DOI handling

---

**PDFs automatically attached for open access papers!** 📄✨
