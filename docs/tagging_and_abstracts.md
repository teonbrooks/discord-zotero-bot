# Tagging and Abstract Cleaning Features

## Overview

This document describes two important features added to the Zotero Discord Bot:
1. **Clean Abstracts** - Removes XML/HTML tags from abstracts
2. **Automatic Tagging** - Tags all items with bot identifier and channel name

## 1. Clean Abstracts

### Problem
CrossRef and other metadata sources often return abstracts with XML/HTML markup:

```xml
<jats:title>Abstract</jats:title><jats:p>Sleep is a fundamental biological process...</jats:p>
```

This made abstracts hard to read in Zotero.

### Solution
Implemented `strip_html_tags()` function that:
- Removes all XML/HTML tags (e.g., `<jats:title>`, `<p>`, `</jats:p>`)
- Cleans up extra whitespace
- Preserves the actual text content

### Example

**Before** (with XML tags):
```
<jats:title>Abstract</jats:title><jats:p>Sleep is a fundamental biological 
process with broad implications for physical and mental health, yet its complex 
relationship with disease remains poorly understood.</jats:p>
```

**After** (clean):
```
Sleep is a fundamental biological process with broad implications for 
physical and mental health, yet its complex relationship with disease remains 
poorly understood.
```

Note: The title tag (`<jats:title>Abstract</jats:title>`) and its content are completely removed, leaving only the paragraph content.

### Technical Details

The function uses regex to strip tags in two steps:

1. **Remove title tags completely** (including their content)
2. **Strip remaining HTML/XML tags** (keeping content)

```python
def strip_html_tags(text: str) -> str:
    """Remove HTML/XML tags from text, keeping only the text content."""
    if not text:
        return ''
    
    # First, remove title tags and their content completely
    # Matches <jats:title>...</jats:title>, <title>...</title>, etc.
    clean_text = re.sub(
        r'<[^>]*title[^>]*>.*?</[^>]*title[^>]*>', 
        '', 
        text, 
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove remaining XML/HTML tags, replacing with space
    clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
    
    # Clean up extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Remove leading/trailing whitespace
    return clean_text.strip()
```

**Why remove titles?**
- Abstracts often include `<jats:title>Abstract</jats:title>` which is redundant
- The actual abstract content is in the `<jats:p>` paragraph tags
- Removing the title makes abstracts cleaner and more readable

### Applied To

The cleaning is applied to abstracts from:
- ✅ CrossRef (DOI metadata)
- ✅ arXiv papers
- ✅ Any other source that returns HTML/XML in abstracts

### Title Tag Formats Handled

The function removes various title tag formats:
- `<jats:title>Abstract</jats:title>` (JATS format - Nature, Science, etc.)
- `<title>Summary</title>` (Generic HTML)
- `<TITLE>ABSTRACT</TITLE>` (Case insensitive)
- Nested titles within sections like `<jats:sec><jats:title>Background</jats:title>...</jats:sec>`

All of these are completely removed, leaving only the paragraph content.

## 2. Automatic Tagging

### Purpose

Tags help organize and track papers in your Zotero library by:
- Identifying which papers were added by the bot
- Showing which Discord channel each paper came from
- Enabling filtering and searching by source

### Tags Applied

Every paper added to Zotero gets **two tags**:

#### Tag 1: Bot Identifier
**`discord-zotero-bot`**

- Applied to every item the bot adds
- Helps distinguish bot-added papers from manual additions
- Useful for filtering and statistics

#### Tag 2: Channel Name
**The Discord channel name** (e.g., `machine-learning`, `papers-to-read`)

- Shows where the paper was shared
- Helps organize papers by topic/community
- Enables channel-specific searches

### Example

Paper posted in `#machine-learning` channel:

```
Title: A multimodal sleep foundation model for disease prediction
Authors: Thapa, R.; Kjaer, M.R.; He, B.; et al.
Publication: Nature Medicine
DOI: 10.1038/s41591-025-04133-4
Tags: 
  - discord-zotero-bot
  - machine-learning
```

### Technical Implementation

Tags are added as an array of objects in Zotero's API format:

```python
# Prepare tags
tags = ['discord-zotero-bot']
if channel_name:
    tags.append(channel_name)

# Add to template
template['tags'] = [{'tag': tag} for tag in tags]
```

### How It Works

1. **Message received** in a channel under the "papers" category
2. **Extract channel name** from Discord message object
3. **Process paper link** and fetch metadata
4. **Add tags** to the Zotero item template:
   - Always: `discord-zotero-bot`
   - If available: channel name
5. **Create item** in Zotero with tags included

### Tag Flow Diagram

```
Discord Message
    ↓
Extract channel name ("machine-learning")
    ↓
Process paper link
    ↓
Fetch metadata (title, authors, etc.)
    ↓
Prepare tags:
  - "discord-zotero-bot"
  - "machine-learning"
    ↓
Create Zotero item with tags
    ↓
Paper saved with tags applied
```

## Using Tags in Zotero

### Filtering by Tag

**Show all bot-added papers:**
1. Open Zotero
2. Click on `discord-zotero-bot` tag in left sidebar
3. See all papers added by the bot

**Show papers from specific channel:**
1. Click on channel name tag (e.g., `machine-learning`)
2. See all papers shared in that channel

**Combine filters:**
1. Hold Ctrl/Cmd and click multiple tags
2. See papers matching all selected tags

### Organizing with Tag Colors

Assign colors to important channel tags:
1. Right-click a channel tag
2. Select "Assign Color"
3. Choose a color
4. Papers with that tag will show the color indicator

Example color scheme:
- 🔴 `high-priority` - Red
- 🔵 `machine-learning` - Blue
- 🟢 `neuroscience` - Green
- 🟡 `papers-to-read` - Yellow

### Searching by Tags

Use Zotero's search:
1. Advanced Search → "Tag" → "is" → "machine-learning"
2. Create saved searches for frequently used tags
3. Export papers by tag

### Managing Tags

**Rename a channel tag:**
1. Right-click the tag
2. Select "Rename Tag"
3. All papers with that tag will be updated

**Delete a tag:**
1. Right-click the tag
2. Select "Delete Tag"
3. Tag removed from all papers (papers remain)

**Merge tags:**
1. Drag one tag onto another
2. Zotero combines them

## Benefits

### For Organization
- ✅ Papers grouped by Discord channel/topic
- ✅ Easy to find papers from specific communities
- ✅ Visual organization with tag colors

### For Discovery
- ✅ See what papers were popular in each channel
- ✅ Track engagement across different communities
- ✅ Find related papers shared in same channel

### For Analysis
- ✅ Count papers from each channel
- ✅ Export channel-specific bibliographies
- ✅ Track bot usage over time

### For Collaboration
- ✅ Share collections filtered by channel
- ✅ Create reading lists from specific communities
- ✅ Identify trending topics by channel

## Examples

### Example 1: ML Papers Collection

Papers shared in `#machine-learning`:

```
1. Paper A - Tags: discord-zotero-bot, machine-learning
2. Paper B - Tags: discord-zotero-bot, machine-learning
3. Paper C - Tags: discord-zotero-bot, machine-learning

Filter: Click "machine-learning" → See all 3 papers
Export: Right-click → Create Bibliography
```

### Example 2: Multi-Channel Paper

Same paper shared in two channels:

**First share** in `#machine-learning`:
```
Tags: discord-zotero-bot, machine-learning
```

**Second share** in `#deep-learning`:
```
Bot detects duplicate → Reacts with ✅
(Tags remain: discord-zotero-bot, machine-learning)
```

Only added once with tags from first channel.

### Example 3: Bot Statistics

How many papers has the bot added?

1. Click `discord-zotero-bot` tag
2. Status bar shows: "X items selected"
3. That's how many papers the bot has added total

## Implementation Notes

### Code Changes

**Files Modified:**
- `zotero-bot.py` - Added `strip_html_tags()` function
- `zotero-bot.py` - Updated all `add_to_zotero_*` functions to accept tags
- `zotero-bot.py` - Updated `process_link()` to prepare tags
- `zotero-bot.py` - Updated `process_message_for_papers()` to extract channel name

**Functions Updated:**
- `add_to_zotero_by_identifier()` - Now accepts `tags` parameter
- `add_to_zotero_by_url()` - Now accepts `tags` parameter
- `process_link()` - Now accepts `channel_name` parameter
- `process_message_for_papers()` - Extracts channel name from message

### Tag Format

Zotero expects tags in this format:
```python
template['tags'] = [
    {'tag': 'discord-zotero-bot'},
    {'tag': 'machine-learning'}
]
```

### Error Handling

- If channel name cannot be determined, only `discord-zotero-bot` tag is added
- Empty channel names are not added as tags
- Tags are sanitized (whitespace normalized)

## Testing

### Test Tag Addition

1. Post a paper in a channel under "papers" category
2. Check Zotero - item should have both tags
3. Verify tags are searchable and filterable

### Test Abstract Cleaning

1. Post a DOI that has XML in abstract (e.g., Nature papers)
2. Check Zotero abstract field
3. Verify no XML tags are present
4. Verify text is readable

### Test Edge Cases

**No channel name:**
- Bot processes message outside normal flow
- Should still add `discord-zotero-bot` tag

**Special characters in channel name:**
- Channel: `ml-&-ai`
- Tag should be: `ml-&-ai` (preserved)

**Long channel names:**
- Zotero handles long tag names
- No truncation needed

## Future Enhancements

### Possible Additions

1. **Custom tag prefixes** - Environment variable to customize bot tag
2. **Category tags** - Add category name as tag too
3. **Date tags** - Add year/month tags for temporal organization
4. **User tags** - Tag papers with Discord username who shared it
5. **Reaction-based tags** - Let users react to add custom tags

### Configuration Ideas

Add to `.env`:
```bash
# Custom bot tag name
BOT_TAG=my-bot

# Add category as tag
TAG_CATEGORY=true

# Add date tags
TAG_DATE=true

# Tag format: prefix-channel vs just channel
TAG_PREFIX=discord
```

## Conclusion

The combination of clean abstracts and automatic tagging makes the bot much more useful:
- **Clean abstracts** ensure papers are readable in Zotero
- **Automatic tags** provide organization and discoverability
- **Channel tags** track paper sources and communities

All papers are now properly organized and easy to find! 🏷️
