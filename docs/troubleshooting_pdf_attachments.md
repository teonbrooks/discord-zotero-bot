# Troubleshooting PDF Attachments

## Problem: PDFs Not Appearing in Zotero

If PDFs are being downloaded but not appearing in your Zotero library, follow these steps:

### Step 1: Check Bot Logs

Look for these log messages in your bot output:

**Download succeeded:**
```
INFO - Successfully downloaded PDF (1234567 bytes)
```

**Attachment attempt:**
```
INFO - Attempting attachment using attachment_simple (parentid=ABCD1234)
```

**Success or failure:**
```
INFO - ✓ Verified: PDF attachment exists for item ABCD1234
```
or
```
WARNING - attachment_simple failed: [error message]
INFO - Attempting manual attachment creation for item ABCD1234
```

### Step 2: Run Diagnostic Test

```bash
cd tests
uv run python test_zotero_attachment.py
```

This will test both attachment methods and tell you which one works.

**Expected output:**
```
Method 1: Testing attachment_simple()...
  ✓ attachment_simple() succeeded
  
Method 2: Testing manual attachment creation...
  ✓ Manual method succeeded
  
✅ At least one method succeeded!
```

### Step 3: Check Zotero API Permissions

Your Zotero API key needs these permissions:

1. Go to: https://www.zotero.org/settings/keys
2. Find your API key
3. Check it has these permissions:
   - ✅ **Write access** to library
   - ✅ **File editing** (important!)
   - ✅ **Allow library access**

**To fix**: Create a new API key with correct permissions:
1. Delete old key
2. Create new key with "Allow library access" and "Allow file editing"
3. Update `ZOTERO_TOKEN` in `.env` file
4. Restart bot

### Step 4: Verify Zotero Storage

Check you haven't exceeded storage quota:

1. Go to: https://www.zotero.org/settings/storage
2. Check available space
3. Free plan: 300 MB limit

**If quota exceeded:**
- Delete old attachments
- Upgrade to paid plan
- Use file syncing instead of Zotero storage

### Step 5: Check Item Types

Attachments can only be added to certain item types:

✅ **Works:**
- Journal Article
- Preprint
- Book
- Conference Paper
- Report

❌ **Doesn't work:**
- Attachments (can't attach to attachments)
- Notes
- Collections

### Step 6: Test Manual Attachment in Zotero

Try manually attaching a file in Zotero to verify your account works:

1. Open Zotero desktop app
2. Select any item
3. Click "Add Attachment" → "Attach Stored Copy of File"
4. Select a PDF

**If this fails:** Your Zotero account/API key has issues
**If this works:** Bot configuration issue

## Common Issues & Solutions

### Issue 1: "attachment_simple failed"

**Symptoms:**
```
WARNING - attachment_simple failed: [error]
INFO - Attempting manual attachment creation
```

**Cause:** Old pyzotero version or API incompatibility

**Solution:** Bot automatically falls back to manual method. This is normal if you see the manual method succeeding.

### Issue 2: "Failed to create attachment item"

**Symptoms:**
```
ERROR - Failed to create attachment item: {created}
```

**Possible causes:**
1. **API key lacks write/file permissions**
   - Solution: Create new API key with full permissions
2. **Invalid parent item**
   - Solution: Check item exists and is correct type
3. **Network issues**
   - Solution: Check internet connection, retry

### Issue 3: PDFs Download But Don't Attach

**Symptoms:**
```
INFO - Successfully downloaded PDF (1234567 bytes)
INFO - Attempting attachment...
[no success message]
```

**Debugging:**
1. Check full bot logs for errors
2. Run diagnostic test: `python tests/test_zotero_attachment.py`
3. Check Zotero web interface - is item there?
4. Check Zotero storage quota

**Likely cause:** API permissions issue

### Issue 4: "No attachment found" After Success

**Symptoms:**
```
INFO - attachment_simple succeeded
WARNING - attachment_simple returned success but no attachment found
```

**Cause:** API call succeeded but attachment didn't persist

**Solutions:**
1. Check Zotero web interface directly
2. Wait a few seconds and refresh
3. Check if attachment is in trash
4. Try manual method (bot does this automatically)

### Issue 5: Timeouts

**Symptoms:**
```
WARNING - Timeout while downloading PDF from [url]
```

**Causes:**
- Slow internet connection
- Large PDF files (>50MB)
- Server slow to respond

**Solutions:**
- Retry later
- Check network connection
- Large files may need manual download

## Advanced Debugging

### Enable Debug Logging

Edit `zotero-bot.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

This shows all API calls and responses.

### Check Zotero API Directly

Test your API key manually:

```bash
curl -H "Zotero-API-Key: YOUR_KEY" \
  https://api.zotero.org/groups/YOUR_GROUP_ID/items?limit=1
```

Should return JSON with items. If error, API key is invalid.

### Verify pyzotero Version

```bash
uv run python -c "import pyzotero; print(pyzotero.__version__)"
```

Should be 1.5.0 or newer.

### Check File Permissions

Bot needs write access to temp directory:

```bash
python -c "import tempfile; print(tempfile.gettempdir())"
```

Verify this directory is writable.

## Still Not Working?

### Collect Debug Information

1. **Bot logs** - Full output including errors
2. **Test output** - Run `python tests/test_zotero_attachment.py`
3. **API permissions** - Screenshot from Zotero settings
4. **Storage quota** - How much space used
5. **Zotero version** - Web or desktop app version

### Try These Workarounds

**Workaround 1: Manual Download**
1. Bot adds metadata
2. Manually download PDF
3. Drag and drop onto Zotero item

**Workaround 2: Zotero Connector**
1. Visit paper webpage
2. Use Zotero Connector browser extension
3. It may grab PDF automatically

**Workaround 3: Update PDF Links**
1. Bot adds item with metadata
2. PDF URL stored in item's URL field
3. Use Zotero's "Find Available PDF" feature

## Configuration Checklist

Go through this checklist:

- [ ] Bot has internet access
- [ ] `.env` file has valid `ZOTERO_TOKEN`
- [ ] `.env` file has valid `ZOTERO_GROUP_ID`
- [ ] API key has "Allow library access" permission
- [ ] API key has "Allow file editing" permission
- [ ] Zotero storage has available space
- [ ] Bot is restarted after code changes
- [ ] pyzotero is installed (`uv run python -c "import pyzotero"`)
- [ ] Items in library are valid types (not notes/attachments)

## Technical Details

### Two Attachment Methods

The bot tries two methods automatically:

**Method 1: `attachment_simple()`**
```python
zot.attachment_simple([pdf_path], parentid=item_key)
```
- Simpler, one API call
- May not work with all pyzotero versions

**Method 2: Manual creation**
```python
# Create attachment item
template = zot.item_template('attachment', 'imported_file')
template['parentItem'] = item_key
created = zot.create_items([template])

# Upload file
attachment_key = created['successful']['0']['key']
zot.upload_attachment(attachment_key, pdf_file)
```
- More complex, two API calls
- More reliable
- Bot uses this as fallback

### Verification

After attachment, bot verifies:
```python
children = zot.children(item_key)
has_pdf = any(c['data'].get('itemType') == 'attachment' for c in children)
```

If verification fails but API call succeeded, might be timing issue.

## Getting Help

If nothing works, provide:

1. Output of: `python tests/test_zotero_attachment.py`
2. Bot log snippet showing attachment attempt
3. Zotero API permissions screenshot
4. Storage quota status
5. Item type you're trying to attach to

Check bot logs carefully - the error message usually tells you exactly what's wrong!
