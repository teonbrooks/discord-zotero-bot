# Debugging Duplicate Issues

If you're still experiencing duplicates, follow this guide to diagnose and fix the issue.

## Step 1: Run the Test Script

We've created a test script to help diagnose duplicate detection issues:

```bash
cd /Users/teonbrooks/codespace/zotero-bot
uv run python test_duplicates.py
```

This script will:
1. Show your recent library items
2. Let you manually test if DOIs/URLs are being found
3. Help identify why duplicates might not be detected

### Example Test Session

```
Options:
1. Test DOI search
2. Test URL search
3. Show library contents again
4. Exit

Enter choice (1-4): 1
Enter DOI to check: 10.1038/s41591-025-04133-4
```

The script will show:
- Whether the DOI was found via text search
- Whether the DOI was found in recent items
- What items were returned by the search

## Step 2: Check Bot Logs

When running the bot, watch the console output carefully. You should see:

### When Adding a NEW Paper
```
INFO - Checking for duplicate DOI: 10.1038/s41591-025-04133-4
DEBUG - Comprehensive duplicate check - DOI: 10.1038/s41591-025-04133-4...
DEBUG - Checking DOI: 10.1038/s41591-025-04133-4
DEBUG - No duplicate found
INFO - No duplicate found, fetching metadata for DOI: 10.1038/s41591-025-04133-4
INFO - Added item with DOI and metadata: 10.1038/s41591-025-04133-4
INFO - Added 1 paper(s) from message 123456789
```

### When Finding a DUPLICATE
```
INFO - Checking for duplicate DOI: 10.1038/s41591-025-04133-4
DEBUG - Comprehensive duplicate check - DOI: 10.1038/s41591-025-04133-4...
DEBUG - Checking DOI: 10.1038/s41591-025-04133-4
INFO - Found existing item with DOI: 10.1038/s41591-025-04133-4
INFO - Duplicate found via DOI: 10.1038/s41591-025-04133-4
INFO - Duplicate found for DOI: 10.1038/s41591-025-04133-4
INFO - Found 1 duplicate(s) in message 123456789
```

## Step 3: Enable Debug Logging

For more detailed logs, edit `zotero-bot.py` and change the logging level:

```python
# Find this line near the top:
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Change to:
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

This will show DEBUG messages including all duplicate checks being performed.

## Common Issues and Solutions

### Issue 1: Duplicates Being Added Before Search Completes

**Symptom**: Same paper added twice quickly

**Cause**: Both messages processed simultaneously before first is committed to Zotero

**Solution**: The bot processes messages sequentially, but Zotero API might have delay in indexing. Add a small delay after adding items:

In the code, after `zot.create_items([template])`, add:
```python
await asyncio.sleep(1)  # Give Zotero time to index
```

### Issue 2: Text Search Not Finding Items

**Symptom**: Test script shows item exists in recent items but not in text search

**Cause**: Zotero's text search (`q` parameter) doesn't always index DOI field immediately

**Fix**: The updated code now checks both text search AND recent items (up to 100 items). If your library is larger than 100 items and duplicates are older, you may need to increase the `top(limit=100)` to a higher number.

### Issue 3: Large Library Performance

**Symptom**: Slow duplicate checking or missed duplicates in large libraries

**Solution**: Increase the limits in search functions:

In `search_zotero_by_doi` and `search_zotero_by_url`:
```python
recent_items = zot.top(limit=100)  # Change to 200 or 300
```

**Trade-off**: Higher limits = slower but more thorough checking

### Issue 4: Different DOI Formats

**Symptom**: Same paper with DOI in different formats (`10.1038/...` vs `10.1038/...` with extra characters)

**Check**: Run test script and see exact DOI format stored in Zotero

**Solution**: The code normalizes DOIs (lowercase, trimmed), but if there are other variations, we may need custom normalization.

## Step 4: Manual Testing

### Test Same Paper, Different URLs

1. Add a paper via DOI:
   ```
   Post in Discord: https://doi.org/10.1038/s41591-025-04133-4
   ```
   Watch logs: Should say "Added item with DOI"

2. Add same paper via journal URL:
   ```
   Post in Discord: https://www.nature.com/articles/s41591-025-04133-4
   ```
   Watch logs: Should say "Found existing item with DOI" and react with ✅

3. Check Discord:
   - First message: 🤖 emoji
   - Second message: ✅ emoji

4. Check Zotero:
   - Should have ONE entry, not two

### If Still Getting Duplicates

Look at the logs and identify:
1. Which check is failing? (DOI, URL, or title)
2. Is the paper being found in text search?
3. Is the paper being found in recent items?

Run `test_duplicates.py` with the exact DOI/URL that's creating duplicates and share the output.

## Step 5: Temporary Workaround

If duplicates persist and you need an immediate solution:

### Option A: Increase Search Thoroughness

Edit `zotero-bot.py` and increase all limits:

```python
# In search_zotero_by_doi:
recent_items = zot.top(limit=300)  # was 100

# In search_zotero_by_url:
recent_items = zot.top(limit=300)  # was 100
```

This checks more items but is slower.

### Option B: Add Post-Creation Delay

After creating items, add delay to let Zotero index:

```python
# After zot.create_items([template]):
items = zot.create_items([template])
await asyncio.sleep(2)  # Wait for Zotero to index
logger.info(f"Added item with DOI and metadata: {identifier}")
```

### Option C: Check All Items (Slow but Thorough)

For very large libraries, you might need to check ALL items:

```python
def search_zotero_by_doi(doi: str) -> bool:
    normalized_doi = doi.strip().lower()
    
    # Get ALL items (warning: slow for large libraries!)
    all_items = zot.everything(zot.top())
    
    for item in all_items:
        item_doi = item.get('data', {}).get('DOI', '').strip().lower()
        if item_doi == normalized_doi:
            return True
    
    return False
```

## Reporting Issues

If duplicates persist after trying these steps, please provide:

1. **Output from test script** showing the duplicate DOI/URL
2. **Bot logs** showing the duplicate being added (with DEBUG enabled)
3. **Library size** (approximate number of items)
4. **Example** of exact URLs/DOIs that created duplicates

This will help diagnose the specific issue with your setup.

## Quick Checklist

- [ ] Ran `test_duplicates.py` to verify searches work
- [ ] Enabled DEBUG logging in bot
- [ ] Checked logs for "Found existing item" messages
- [ ] Verified emoji reactions (🤖 vs ✅)
- [ ] Tried increasing search limits
- [ ] Restarted bot after making changes
- [ ] Tested with fresh example (not previously cached)
