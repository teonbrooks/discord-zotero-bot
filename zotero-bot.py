import os
import re
import logging
from typing import List, Dict, Set, Tuple, Optional
import asyncio

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from pyzotero import zotero

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ZOTERO_TOKEN = os.getenv("ZOTERO_TOKEN")
ZOTERO_GROUP_ID = os.getenv("ZOTERO_GROUP_ID")
PAPERS_CATEGORY_NAME = os.getenv("PAPERS_CATEGORY_NAME", "papers")
MAX_MESSAGES_PER_CHANNEL = int(os.getenv("MAX_MESSAGES_PER_CHANNEL", "100"))

# Emoji configuration
SUCCESS_EMOJI = "🤖"
DUPLICATE_EMOJI = "✅"
ERROR_EMOJI = "❌"

# Validate required environment variables
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")
if not ZOTERO_TOKEN:
    raise ValueError("ZOTERO_TOKEN environment variable is required")
if not ZOTERO_GROUP_ID:
    raise ValueError("ZOTERO_GROUP_ID environment variable is required")

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Zotero client
zot = zotero.Zotero(ZOTERO_GROUP_ID, 'group', ZOTERO_TOKEN)


# ============================================================================
# Link Extraction Functions
# ============================================================================

def extract_urls_from_message(content: str) -> List[str]:
    """Extract all URLs from message content."""
    # Regex to match http/https URLs
    url_pattern = r'https?://[^\s<>"\'\)]+(?:\([^\s<>"\'\)]*\))*[^\s<>"\'\)\.,;:]?'
    urls = re.findall(url_pattern, content)
    return urls


def extract_doi(text: str) -> Optional[str]:
    """Extract DOI from text or URL."""
    # Match DOI patterns
    doi_patterns = [
        r'(?:https?://)?(?:dx\.)?doi\.org/(10\.\S+)',
        r'\b(10\.\d{4,}(?:\.\d+)*(?:/|%2F)[^\s]+)',
    ]
    
    for pattern in doi_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            doi = match.group(1)
            # Clean up DOI
            doi = doi.rstrip('.,;:)')
            return doi
    return None


def extract_arxiv_id(text: str) -> Optional[str]:
    """Extract arXiv ID from text or URL."""
    # Match arXiv patterns
    arxiv_patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b',
    ]
    
    for pattern in arxiv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_pubmed_id(text: str) -> Optional[str]:
    """Extract PubMed ID from text or URL."""
    # Match PubMed patterns
    pubmed_patterns = [
        r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)',
        r'ncbi\.nlm\.nih\.gov/pubmed/(\d+)',
        r'\bPMID:?\s*(\d+)\b',
    ]
    
    for pattern in pubmed_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def is_pdf_url(url: str) -> bool:
    """Check if URL points to a PDF file."""
    return url.lower().endswith('.pdf') or '.pdf?' in url.lower()


def categorize_link(url: str) -> Tuple[str, Optional[str]]:
    """
    Categorize a link and extract identifier if applicable.
    Returns (type, identifier) where type is one of: 'doi', 'arxiv', 'pubmed', 'pdf', 'generic'
    """
    # Check for DOI
    doi = extract_doi(url)
    if doi:
        return ('doi', doi)
    
    # Check for arXiv
    arxiv_id = extract_arxiv_id(url)
    if arxiv_id:
        return ('arxiv', arxiv_id)
    
    # Check for PubMed
    pubmed_id = extract_pubmed_id(url)
    if pubmed_id:
        return ('pubmed', pubmed_id)
    
    # Check for PDF
    if is_pdf_url(url):
        return ('pdf', url)
    
    # Generic URL
    return ('generic', url)


# ============================================================================
# Zotero Integration Functions
# ============================================================================

def search_zotero_by_doi(doi: str) -> bool:
    """Check if item with DOI already exists in Zotero library."""
    try:
        results = zot.items(q=doi, limit=5)
        for item in results:
            item_doi = item.get('data', {}).get('DOI', '')
            if item_doi and item_doi.lower() == doi.lower():
                return True
        return False
    except Exception as e:
        logger.error(f"Error searching Zotero by DOI: {e}")
        return False


def search_zotero_by_url(url: str) -> bool:
    """Check if item with URL already exists in Zotero library."""
    try:
        results = zot.items(q=url, limit=5)
        for item in results:
            item_url = item.get('data', {}).get('url', '')
            if item_url and item_url.lower() == url.lower():
                return True
        return False
    except Exception as e:
        logger.error(f"Error searching Zotero by URL: {e}")
        return False


def search_zotero_by_title(title: str) -> bool:
    """Check if item with similar title already exists in Zotero library."""
    try:
        results = zot.items(q=title, limit=5)
        if results:
            # Simple check - if we get results with the title query
            return True
        return False
    except Exception as e:
        logger.error(f"Error searching Zotero by title: {e}")
        return False


async def add_to_zotero_by_identifier(identifier_type: str, identifier: str) -> Tuple[bool, str]:
    """
    Add item to Zotero by identifier (DOI, arXiv ID, PMID).
    Returns (success, message)
    """
    try:
        # Check for duplicates
        if identifier_type == 'doi':
            if search_zotero_by_doi(identifier):
                return (False, "duplicate")
        
        # Create item template
        template = zot.item_template('journalArticle')
        
        # Add identifier to appropriate field
        if identifier_type == 'doi':
            template['DOI'] = identifier
            # Try to fetch metadata from DOI
            try:
                items = zot.create_items([template])
                logger.info(f"Added item with DOI: {identifier}")
                return (True, "success")
            except Exception as e:
                logger.error(f"Error adding DOI: {e}")
                return (False, str(e))
        
        elif identifier_type == 'arxiv':
            # For arXiv, we'll use the URL approach
            url = f"https://arxiv.org/abs/{identifier}"
            return await add_to_zotero_by_url(url)
        
        elif identifier_type == 'pubmed':
            # For PubMed, we'll use the URL approach
            url = f"https://pubmed.ncbi.nlm.nih.gov/{identifier}/"
            return await add_to_zotero_by_url(url)
        
        return (False, "unsupported_identifier_type")
        
    except Exception as e:
        logger.error(f"Error adding item by identifier: {e}")
        return (False, str(e))


async def add_to_zotero_by_url(url: str) -> Tuple[bool, str]:
    """
    Add item to Zotero by URL using web translator.
    Returns (success, message)
    """
    try:
        # Check for duplicates by URL
        if search_zotero_by_url(url):
            return (False, "duplicate")
        
        # Try to create item from URL
        # Pyzotero doesn't directly support web translators,
        # so we'll create a webpage item with the URL
        template = zot.item_template('webpage')
        template['url'] = url
        template['title'] = f"Paper from {url}"
        
        # Add note that this should be enriched
        template['extra'] = f"Added from Discord bot. Original URL: {url}"
        
        try:
            items = zot.create_items([template])
            logger.info(f"Added item from URL: {url}")
            return (True, "success")
        except Exception as e:
            logger.error(f"Error adding URL: {e}")
            return (False, str(e))
        
    except Exception as e:
        logger.error(f"Error adding item by URL: {e}")
        return (False, str(e))


async def process_link(url: str) -> Tuple[bool, bool]:
    """
    Process a single link and add to Zotero if not duplicate.
    Returns (was_added, is_duplicate)
    """
    link_type, identifier = categorize_link(url)
    
    logger.info(f"Processing link: {url} (type: {link_type})")
    
    try:
        if link_type in ['doi', 'arxiv', 'pubmed']:
            success, message = await add_to_zotero_by_identifier(link_type, identifier)
        else:  # pdf or generic
            success, message = await add_to_zotero_by_url(url)
        
        if message == "duplicate":
            return (False, True)
        elif success:
            return (True, False)
        else:
            return (False, False)
            
    except Exception as e:
        logger.error(f"Error processing link {url}: {e}")
        return (False, False)


# ============================================================================
# Discord Helper Functions
# ============================================================================

def is_in_papers_category(channel: discord.TextChannel) -> bool:
    """Check if channel is in the papers category."""
    if not isinstance(channel, discord.TextChannel):
        return False
    
    if channel.category:
        return channel.category.name.lower() == PAPERS_CATEGORY_NAME.lower()
    
    return False


async def process_message_for_papers(message: discord.Message) -> Dict[str, int]:
    """
    Process a message for paper links and add them to Zotero.
    Returns statistics: {'added': count, 'duplicates': count, 'errors': count}
    """
    stats = {'added': 0, 'duplicates': 0, 'errors': 0}
    
    # Extract URLs from message
    urls = extract_urls_from_message(message.content)
    
    if not urls:
        return stats
    
    # Process each URL
    processed_urls: Set[str] = set()
    
    for url in urls:
        if url in processed_urls:
            continue
        processed_urls.add(url)
        
        try:
            was_added, is_duplicate = await process_link(url)
            
            if was_added:
                stats['added'] += 1
                try:
                    await message.add_reaction(SUCCESS_EMOJI)
                except discord.errors.Forbidden:
                    logger.warning(f"Cannot add reaction to message {message.id}")
            elif is_duplicate:
                stats['duplicates'] += 1
                try:
                    await message.add_reaction(DUPLICATE_EMOJI)
                except discord.errors.Forbidden:
                    logger.warning(f"Cannot add reaction to message {message.id}")
            else:
                stats['errors'] += 1
                
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            stats['errors'] += 1
    
    return stats


# ============================================================================
# Discord Bot Events
# ============================================================================

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    await bot.tree.sync()
    logger.info(f"{bot.user} is online!")
    logger.info(f"Monitoring category: {PAPERS_CATEGORY_NAME}")
    logger.info(f"Zotero Group ID: {ZOTERO_GROUP_ID}")


@bot.event
async def on_message(message: discord.Message):
    """Process messages in real-time."""
    # Ignore bot's own messages
    if message.author.id == bot.user.id:
        return
    
    # Check if message is in papers category
    if not is_in_papers_category(message.channel):
        return
    
    # Process the message for paper links
    stats = await process_message_for_papers(message)
    
    if stats['added'] > 0:
        logger.info(f"Added {stats['added']} paper(s) from message {message.id}")
    if stats['duplicates'] > 0:
        logger.info(f"Found {stats['duplicates']} duplicate(s) in message {message.id}")
    if stats['errors'] > 0:
        logger.warning(f"Had {stats['errors']} error(s) processing message {message.id}")
    
    # Process commands
    await bot.process_commands(message)


# ============================================================================
# Discord Bot Commands
# ============================================================================

@bot.tree.command(name="scan_papers", description="Scan papers category channels for article links")
@app_commands.describe(
    limit="Maximum number of messages to scan per channel (default: 100)"
)
async def scan_papers(interaction: discord.Interaction, limit: int = None):
    """Scan all channels in papers category and add papers to Zotero."""
    await interaction.response.defer(thinking=True)
    
    if limit is None:
        limit = MAX_MESSAGES_PER_CHANNEL
    
    # Validate limit
    if limit < 1 or limit > 1000:
        await interaction.followup.send("❌ Limit must be between 1 and 1000")
        return
    
    try:
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ This command must be used in a server")
            return
        
        # Find papers category
        papers_category = None
        for category in guild.categories:
            if category.name.lower() == PAPERS_CATEGORY_NAME.lower():
                papers_category = category
                break
        
        if not papers_category:
            await interaction.followup.send(f"❌ Could not find '{PAPERS_CATEGORY_NAME}' category")
            return
        
        # Get all text channels in the category
        channels = [ch for ch in papers_category.channels if isinstance(ch, discord.TextChannel)]
        
        if not channels:
            await interaction.followup.send(f"❌ No text channels found in '{PAPERS_CATEGORY_NAME}' category")
            return
        
        await interaction.followup.send(
            f"🔍 Starting scan of {len(channels)} channel(s) in '{PAPERS_CATEGORY_NAME}' category...\n"
            f"Scanning up to {limit} messages per channel."
        )
        
        # Process each channel
        total_stats = {'added': 0, 'duplicates': 0, 'errors': 0, 'messages': 0}
        
        for channel in channels:
            channel_stats = {'added': 0, 'duplicates': 0, 'errors': 0, 'messages': 0}
            
            try:
                logger.info(f"Scanning channel: {channel.name}")
                
                # Fetch messages
                async for message in channel.history(limit=limit):
                    if message.author.id == bot.user.id:
                        continue
                    
                    channel_stats['messages'] += 1
                    stats = await process_message_for_papers(message)
                    
                    channel_stats['added'] += stats['added']
                    channel_stats['duplicates'] += stats['duplicates']
                    channel_stats['errors'] += stats['errors']
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                
                # Update totals
                total_stats['added'] += channel_stats['added']
                total_stats['duplicates'] += channel_stats['duplicates']
                total_stats['errors'] += channel_stats['errors']
                total_stats['messages'] += channel_stats['messages']
                
                logger.info(
                    f"Channel {channel.name}: "
                    f"{channel_stats['messages']} messages, "
                    f"{channel_stats['added']} added, "
                    f"{channel_stats['duplicates']} duplicates"
                )
                
            except discord.errors.Forbidden:
                logger.error(f"No permission to read channel: {channel.name}")
            except Exception as e:
                logger.error(f"Error scanning channel {channel.name}: {e}")
        
        # Send summary
        summary = (
            f"✅ **Scan Complete**\n\n"
            f"📊 **Statistics:**\n"
            f"• Messages scanned: {total_stats['messages']}\n"
            f"• Papers added: {total_stats['added']} {SUCCESS_EMOJI}\n"
            f"• Duplicates found: {total_stats['duplicates']} {DUPLICATE_EMOJI}\n"
            f"• Errors: {total_stats['errors']}\n\n"
            f"Check the channel for emoji reactions on messages with papers."
        )
        
        await interaction.followup.send(summary)
        
    except Exception as e:
        logger.error(f"Error in scan_papers command: {e}")
        await interaction.followup.send(f"❌ An error occurred: {str(e)}")


@bot.tree.command(name="zotero_stats", description="Show Zotero library statistics")
async def zotero_stats(interaction: discord.Interaction):
    """Display statistics about the Zotero library."""
    await interaction.response.defer(thinking=True)
    
    try:
        # Get total items count
        items = zot.items(limit=1)
        total_items = zot.num_items()
        
        # Get collection info
        collections = zot.collections()
        num_collections = len(collections)
        
        stats_msg = (
            f"📚 **Zotero Library Statistics**\n\n"
            f"• Total items: {total_items}\n"
            f"• Collections: {num_collections}\n"
            f"• Group ID: {ZOTERO_GROUP_ID}"
        )
        
        await interaction.followup.send(stats_msg)
        
    except Exception as e:
        logger.error(f"Error getting Zotero stats: {e}")
        await interaction.followup.send(f"❌ Error fetching statistics: {str(e)}")


# ============================================================================
# Run Bot
# ============================================================================

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
