# arXiv Troubleshooting Guide

## Summary of Changes

I've made several improvements to help diagnose and fix arXiv issues:

### 1. **Added arXiv DOI Support** ✅ **NEW!**
- Now supports: `https://doi.org/10.48550/arXiv.2404.05553`
- arXiv uses DOI prefix `10.48550/arXiv.*`
- These DOIs are now correctly detected as arXiv papers
- Fixed detection order: arXiv checked BEFORE general DOI

### 2. **Updated API URL to HTTPS** ✅
- Changed: `http://export.arxiv.org` → `https://export.arxiv.org`
- Why: More secure and may be required in some network environments

### 3. **Added Comprehensive Logging** ✅
- Link categorization now logs what type was detected
- arXiv processing logs each step
- Better error messages with stack traces
- Helps identify exactly where issues occur

### 4. **Verified API Functionality** ✅
- Ran live tests - arXiv API is working perfectly
- All test cases passed (4/4)
- Tested with real papers including your "Alljoined1" paper

## How to Diagnose Your Issue

### Step 1: Restart the Bot

After the updates, restart the bot:

```bash
cd /Users/teonbrooks/codespace/zotero-bot
uv run python zotero-bot.py
```

### Step 2: Test with a Known arXiv Paper

Post this in a papers channel:
```
https://arxiv.org/abs/1706.03762
```

This is the famous "Attention Is All You Need" paper - definitely exists!

### Step 3: Watch the Console Logs

You should see logs like this:

**If working correctly**:
```
INFO - Detected arXiv link with ID: 1706.03762
INFO - Processing arXiv paper with ID: 1706.03762
INFO - Successfully parsed arXiv metadata for 1706.03762
INFO - Successfully fetched arXiv metadata for: 1706.03762
INFO - Added arXiv item with metadata: 1706.03762
INFO - Added 1 paper(s) from message 123456789
```

**If there's an issue**, you'll see one of these:
```
WARNING - No entry found in arXiv API response for ID: ...
WARNING - arXiv API returned status XXX for ID: ...
ERROR - Error fetching arXiv metadata for ...: [error details]
```

### Step 4: Common Issues and Solutions

#### Issue 1: "No entry found in arXiv API response"

**Problem**: arXiv ID doesn't exist or is incorrectly formatted

**Check**:
- Is the ID in correct format? (YYMM.NNNNN or YYMM.NNNNNvN)
- Does the paper exist? Try visiting `https://arxiv.org/abs/[ID]`

**Valid formats**:
- ✓ `2401.12345`
- ✓ `1706.03762`
- ✓ `2401.12345v1` (with version)
- ✗ `arxiv.12345` (invalid)

#### Issue 2: "arXiv API returned status 403" or similar

**Problem**: Network/firewall blocking HTTPS requests

**Solution**: Check your network settings or VPN

#### Issue 3: No logs appear at all

**Problem**: Bot not receiving the message or channel not in papers category

**Check**:
- Is the channel under a category named "papers"?
- Is the bot running?
- Does the bot have permissions to read messages?

## Testing Commands

### Test arXiv Extraction
```bash
python test_arxiv_live.py
```

This tests:
- URL extraction
- API connectivity
- Metadata parsing

Expected output: `✅ SUCCESS - Metadata fetched successfully`

### Test Link Categories
Create a test script to check what type your link is being detected as:

```python
import re
from typing import Optional

def extract_arxiv_id(text: str) -> Optional[str]:
    arxiv_patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b',
    ]
    for pattern in arxiv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

# Test your URL
url = "YOUR_ARXIV_URL_HERE"
arxiv_id = extract_arxiv_id(url)
print(f"Input: {url}")
print(f"Extracted ID: {arxiv_id}")
```

## URL Format Examples

### ✅ Supported Formats

All of these should work:

1. **arXiv DOI URL** (NEW!):
   ```
   https://doi.org/10.48550/arXiv.2404.05553
   ```

2. **Standard arXiv URL**:
   ```
   https://arxiv.org/abs/2401.12345
   ```

3. **PDF URL**:
   ```
   https://arxiv.org/pdf/2401.12345.pdf
   ```

4. **Bare ID**:
   ```
   2401.12345
   ```

5. **With version**:
   ```
   https://arxiv.org/abs/2401.12345v1
   ```

6. **Old arXiv format** (pre-2007):
   ```
   https://arxiv.org/abs/hep-th/0601001
   ```
   **Note**: May not work with current regex pattern

### ❌ Formats That Won't Work

1. **Abstract page with extra params**:
   ```
   https://arxiv.org/abs/2401.12345?context=cs
   ```
   Should still work, but params are ignored

2. **Non-arXiv DOIs** (correctly processed as general DOI):
   ```
   https://doi.org/10.1038/s41591-025-04133-4
   ```

## What Gets Created in Zotero

When an arXiv paper is successfully added:

```
Type: Preprint
Title: [Paper title from arXiv]
Authors: [All authors]
Repository: arXiv
Archive ID: 2401.12345
DOI: [If available]
Date: [Publication date]
Abstract: [Clean abstract, no HTML]
URL: https://arxiv.org/abs/2401.12345
Tags:
  - discord-zotero-bot
  - [channel-name]
```

## Still Having Issues?

If arXiv still isn't working after trying the above:

### 1. Share Console Output

Run the bot and post an arXiv link, then share:
- The exact URL you posted
- The console logs (especially lines with "arxiv" in them)
- Any error messages

### 2. Check Bot Logs for These Lines

```bash
# Look for these patterns in the logs:
grep -i "arxiv" bot.log
grep -i "detected.*link" bot.log
grep -i "processing.*paper" bot.log
```

### 3. Test Manually

Run the test script to verify the API is accessible:
```bash
uv run python test_arxiv_live.py
```

If this passes but Discord doesn't work, the issue is with bot permissions or message handling.

### 4. Verify Environment

```bash
# Check Python packages
uv run python -c "import httpx; print('httpx:', httpx.__version__)"
uv run python -c "import pyzotero; print('pyzotero installed')"

# Test network
curl -I https://export.arxiv.org/api/query?id_list=1706.03762
```

## Debug Mode

To enable more verbose logging, edit `zotero-bot.py`:

```python
# Find this line near the top:
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Change to:
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

This will show DEBUG level messages including categorization details.

## Expected Behavior

### Successful arXiv Addition

1. Post: `https://arxiv.org/abs/2401.12345`
2. Bot logs:
   ```
   INFO - Detected arXiv link with ID: 2401.12345
   INFO - Processing arXiv paper with ID: 2401.12345
   INFO - Successfully parsed arXiv metadata for 2401.12345
   INFO - Added arXiv item with metadata: 2401.12345
   ```
3. Discord: Bot reacts with 🤖
4. Zotero: Preprint created with full metadata

### Duplicate Detection

1. Post same paper again
2. Bot logs:
   ```
   INFO - Detected arXiv link with ID: 2401.12345
   INFO - Processing arXiv paper with ID: 2401.12345
   INFO - Successfully fetched arXiv metadata for: 2401.12345
   INFO - arXiv paper 2401.12345 is a duplicate
   INFO - Found 1 duplicate(s) in message 123456789
   ```
3. Discord: Bot reacts with ✅
4. Zotero: No new entry (duplicate skipped)

## Contact Information

If you're still experiencing issues after trying everything above, please provide:

1. The exact arXiv URL you tried
2. Console log output (with sensitive info removed)
3. Result of running `test_arxiv_live.py`
4. Your network setup (e.g., behind corporate firewall, VPN, etc.)

This will help identify if it's:
- A network/firewall issue
- An API issue
- A bot configuration issue
- A Discord permissions issue
