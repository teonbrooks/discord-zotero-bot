# Testing Guide for Zotero Discord Bot

## Pre-Flight Checklist

Before running the bot, ensure:

1. ✅ `.env` file exists with all required variables:
   - `DISCORD_TOKEN`
   - `ZOTERO_TOKEN`
   - `ZOTERO_GROUP_ID`

2. ✅ Discord bot has required permissions:
   - Read Messages/View Channels
   - Send Messages
   - Add Reactions
   - Read Message History
   - Message Content Intent enabled in Discord Developer Portal

3. ✅ Discord server has a "papers" category with at least one channel

4. ✅ Dependencies installed: `uv sync`

## Running the Bot

```bash
cd /Users/teonbrooks/codespace/zotero-bot
uv run python zotero-bot.py
```

You should see:
```
INFO - {BotName} is online!
INFO - Monitoring category: papers
INFO - Zotero Group ID: {your_group_id}
```

## Test Cases

### Test 1: DOI Link Detection
Post in a papers channel:
```
Check out this paper: https://doi.org/10.1038/s41591-025-04133-4
```

**Expected**: Bot reacts with 🤖 (or ✅ if duplicate)

### Test 2: arXiv Link
Post in a papers channel:
```
Interesting: https://arxiv.org/abs/2401.12345
```

**Expected**: Bot reacts with 🤖 (or ✅ if duplicate)

### Test 3: Generic Scholarly URL
Post in a papers channel:
```
https://www.nature.com/articles/s41591-025-04133-4
```

**Expected**: Bot reacts with 🤖 (or ✅ if duplicate)

### Test 4: Multiple Links in One Message
Post in a papers channel:
```
Two papers:
https://doi.org/10.1038/s41591-025-04133-4
https://arxiv.org/abs/2401.12345
```

**Expected**: Bot reacts with appropriate emoji for each link

### Test 5: PubMed Link
Post in a papers channel:
```
https://pubmed.ncbi.nlm.nih.gov/12345678/
```

**Expected**: Bot reacts with 🤖 (or ✅ if duplicate)

### Test 6: PDF Link
Post in a papers channel:
```
https://example.com/paper.pdf
```

**Expected**: Bot reacts with 🤖 (or ✅ if duplicate)

### Test 7: Scan Command
Run slash command:
```
/scan_papers limit:50
```

**Expected**: 
- Bot sends "Starting scan..." message
- Processes messages
- Sends summary with statistics
- Messages with papers have emoji reactions

### Test 8: Statistics Command
Run slash command:
```
/zotero_stats
```

**Expected**: Bot shows library statistics (total items, collections, group ID)

### Test 9: Messages Outside Papers Category
Post the same links in a channel NOT in the papers category.

**Expected**: Bot ignores these messages (no reactions)

### Test 10: Duplicate Detection
Post the same DOI twice in the papers category.

**Expected**:
- First message: 🤖 reaction
- Second message: ✅ reaction

## Verification in Zotero

After testing:

1. Go to your Zotero group library
2. Verify papers were added
3. Check that metadata was extracted correctly
4. Verify no duplicate entries exist

## Common Issues

### Bot doesn't respond
- Check bot is running (look for "is online!" in console)
- Verify channel is in "papers" category
- Check bot has permission to read messages in that channel
- Verify Message Content Intent is enabled

### No emoji reactions
- Check bot has "Add Reactions" permission
- Look for warnings in console logs

### Papers not added to Zotero
- Verify `ZOTERO_TOKEN` and `ZOTERO_GROUP_ID` are correct
- Check console logs for error messages
- Test Zotero credentials manually

### Slash commands not appearing
- Wait a few minutes after bot starts (commands sync on startup)
- Try `/scan_papers` or `/zotero_stats`
- Check bot has application commands permission

## Monitoring Logs

Watch the console for:
- `INFO` messages showing papers being added
- `WARNING` messages for duplicates or permission issues
- `ERROR` messages for failures

Example successful log:
```
INFO - Processing link: https://doi.org/10.1038/... (type: doi)
INFO - Added item with DOI: 10.1038/...
INFO - Added 1 paper(s) from message 123456789
```

## Rate Limiting

The bot includes delays to avoid rate limiting:
- 0.1 second delay between messages during `/scan_papers`
- Zotero API has rate limits (check Zotero documentation)

If you hit rate limits:
- Reduce `MAX_MESSAGES_PER_CHANNEL` in `.env`
- Use smaller `limit` values in `/scan_papers`
- Wait a few minutes before retrying
