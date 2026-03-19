import asyncio
import logging
import os
import re
from typing import Dict, Set

# Point SSL at certifi's CA bundle before any network library is initialised.
# Required when using Python builds (e.g. fbcode) that don't ship system certs.
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import discord
from discord import app_commands
from discord.ext import commands

from config import (
    DISCORD_TOKEN,
    DUPLICATE_EMOJI,
    MAX_MESSAGES_PER_CHANNEL,
    PAPERS_CATEGORY_NAME,
    SUCCESS_EMOJI,
    ZOTERO_GROUP_ID,
)
from extractors import extract_urls_from_message
from library import download_and_attach_pdf, get_pdf_url, process_link, zot

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


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
    stats = {"added": 0, "duplicates": 0, "errors": 0}

    urls = extract_urls_from_message(message.content)

    if not urls:
        return stats

    channel_name = message.channel.name if hasattr(message.channel, "name") else None

    processed_urls: Set[str] = set()

    for url in urls:
        if url in processed_urls:
            continue
        processed_urls.add(url)

        try:
            was_added, is_duplicate = await process_link(url, channel_name=channel_name)

            if was_added:
                stats["added"] += 1
                try:
                    await message.add_reaction(SUCCESS_EMOJI)
                except discord.errors.Forbidden:
                    logger.warning(f"Cannot add reaction to message {message.id}")
            elif is_duplicate:
                stats["duplicates"] += 1
                try:
                    await message.add_reaction(DUPLICATE_EMOJI)
                except discord.errors.Forbidden:
                    logger.warning(f"Cannot add reaction to message {message.id}")
            else:
                stats["errors"] += 1

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            stats["errors"] += 1

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
    if message.author.id == bot.user.id:
        return

    if not is_in_papers_category(message.channel):
        return

    stats = await process_message_for_papers(message)

    if stats["added"] > 0:
        logger.info(f"Added {stats['added']} paper(s) from message {message.id}")
    if stats["duplicates"] > 0:
        logger.info(f"Found {stats['duplicates']} duplicate(s) in message {message.id}")
    if stats["errors"] > 0:
        logger.warning(f"Had {stats['errors']} error(s) processing message {message.id}")

    await bot.process_commands(message)


# ============================================================================
# Discord Bot Commands
# ============================================================================


@bot.tree.command(name="scan_papers", description="Scan papers category channels for article links")
@app_commands.describe(
    limit="Maximum number of messages to scan per channel (default from config, ignored when all_messages=True)",
    all_messages="Scan every message in each channel with no upper limit (default: False)",
)
async def scan_papers(interaction: discord.Interaction, limit: int = None, all_messages: bool = False):
    """Scan all channels in papers category and add papers to Zotero."""
    await interaction.response.defer(thinking=True)

    # Resolve effective history limit: None tells discord.py to fetch everything
    if all_messages:
        history_limit = None
        limit_display = "all"
    else:
        if limit is None:
            limit = MAX_MESSAGES_PER_CHANNEL
        if limit < 1 or limit > 10000:
            await interaction.followup.send("❌ Limit must be between 1 and 10000")
            return
        history_limit = limit
        limit_display = str(limit)

    try:
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ This command must be used in a server")
            return

        papers_category = None
        for category in guild.categories:
            if category.name.lower() == PAPERS_CATEGORY_NAME.lower():
                papers_category = category
                break

        if not papers_category:
            await interaction.followup.send(f"❌ Could not find '{PAPERS_CATEGORY_NAME}' category")
            return

        channels = [ch for ch in papers_category.channels if isinstance(ch, discord.TextChannel)]

        if not channels:
            await interaction.followup.send(f"❌ No text channels found in '{PAPERS_CATEGORY_NAME}' category")
            return

        await interaction.followup.send(
            f"🔍 Starting scan of {len(channels)} channel(s) in '{PAPERS_CATEGORY_NAME}' category...\n"
            f"Scanning {'all' if all_messages else f'up to {limit_display}'} messages per channel."
        )

        total_stats = {"added": 0, "duplicates": 0, "errors": 0, "messages": 0}

        for channel in channels:
            channel_stats = {"added": 0, "duplicates": 0, "errors": 0, "messages": 0}

            try:
                logger.info(f"Scanning channel: {channel.name} (limit={history_limit})")

                async for message in channel.history(limit=history_limit):
                    if message.author.id == bot.user.id:
                        continue

                    channel_stats["messages"] += 1
                    stats = await process_message_for_papers(message)

                    channel_stats["added"] += stats["added"]
                    channel_stats["duplicates"] += stats["duplicates"]
                    channel_stats["errors"] += stats["errors"]

                    await asyncio.sleep(0.1)

                total_stats["added"] += channel_stats["added"]
                total_stats["duplicates"] += channel_stats["duplicates"]
                total_stats["errors"] += channel_stats["errors"]
                total_stats["messages"] += channel_stats["messages"]

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
        zot.items(limit=1)
        total_items = zot.num_items()

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


@bot.tree.command(name="attach_pdfs", description="Scan Zotero library and attach PDFs to items missing them")
@app_commands.describe(limit="Maximum number of items to process (default: 50, max: 200)")
async def attach_pdfs(interaction: discord.Interaction, limit: int = 50):
    """Scan existing Zotero items and attach PDFs where available."""
    await interaction.response.defer(thinking=True)

    if limit < 1:
        await interaction.followup.send("❌ Limit must be at least 1")
        return
    if limit > 200:
        await interaction.followup.send("❌ Limit cannot exceed 200 (to prevent timeouts)")
        return

    try:
        logger.info(f"Starting PDF attachment scan (limit: {limit})")

        status_msg = await interaction.followup.send(
            f"🔍 Scanning Zotero library for items without PDFs...\nChecking up to {limit} items..."
        )

        items = zot.top(limit=limit)
        logger.info(f"Fetched {len(items)} items from Zotero")

        stats = {
            "scanned": 0,
            "has_attachment": 0,
            "no_identifier": 0,
            "pdf_attached": 0,
            "pdf_failed": 0,
            "pdf_unavailable": 0,
        }

        for item in items:
            stats["scanned"] += 1

            if item["data"].get("itemType") in ["attachment", "note"]:
                continue

            item_key = item["key"]
            item_data = item["data"]

            try:
                children = zot.children(item_key)
                has_pdf = any(
                    child["data"].get("itemType") == "attachment"
                    and child["data"].get("contentType") == "application/pdf"
                    for child in children
                )

                if has_pdf:
                    stats["has_attachment"] += 1
                    logger.debug(f"Item {item_key} already has PDF attachment")
                    continue
            except Exception as e:
                logger.error(f"Error checking attachments for {item_key}: {e}")
                continue

            identifier_type = None
            identifier = None
            metadata = None

            if "DOI" in item_data and item_data["DOI"]:
                doi = item_data["DOI"]

                if "10.48550/arXiv." in doi:
                    identifier_type = "arxiv"
                    identifier = doi.split("10.48550/arXiv.")[1]
                elif "10.1101/" in doi:
                    identifier_type = "biorxiv"
                    identifier = doi
                    metadata = {"url": item_data.get("url", "")}
                else:
                    identifier_type = "doi"
                    identifier = doi

            if not identifier and item_data.get("repository") == "arXiv":
                if "archiveID" in item_data:
                    identifier_type = "arxiv"
                    identifier = item_data["archiveID"]
                elif "url" in item_data:
                    url = item_data["url"]
                    arxiv_match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d+\.\d+)", url)
                    if arxiv_match:
                        identifier_type = "arxiv"
                        identifier = arxiv_match.group(1)

            if not identifier and item_data.get("repository") == "bioRxiv":
                if "archiveID" in item_data:
                    identifier_type = "biorxiv"
                    identifier = item_data["archiveID"]
                    metadata = {"url": item_data.get("url", "")}

            if not identifier_type or not identifier:
                stats["no_identifier"] += 1
                logger.debug(f"No identifier found for item {item_key}")
                continue

            pdf_url = get_pdf_url(identifier_type, identifier, metadata)

            if not pdf_url:
                stats["pdf_unavailable"] += 1
                logger.debug(f"No PDF URL available for {identifier_type}: {identifier}")
                continue

            logger.info(f"Attempting to attach PDF for {identifier_type}: {identifier}")
            filename = f"{identifier_type}_{identifier.replace('/', '_')}.pdf"

            success = await download_and_attach_pdf(item_key, pdf_url, filename)

            if success:
                stats["pdf_attached"] += 1
                logger.info(f"✓ Attached PDF for {identifier_type}: {identifier}")
            else:
                stats["pdf_failed"] += 1
                logger.warning(f"✗ Failed to attach PDF for {identifier_type}: {identifier}")

            if stats["scanned"] % 10 == 0:
                try:
                    await status_msg.edit(
                        content=f"🔍 Scanning... {stats['scanned']}/{len(items)} items processed\n"
                        f"📄 PDFs attached: {stats['pdf_attached']}"
                    )
                except Exception:
                    pass

        report = (
            f"✅ **PDF Attachment Scan Complete**\n\n"
            f"📊 **Statistics:**\n"
            f"• Items scanned: {stats['scanned']}\n"
            f"• Already have PDFs: {stats['has_attachment']}\n"
            f"• No identifier found: {stats['no_identifier']}\n"
            f"• PDF not available: {stats['pdf_unavailable']}\n"
            f"• ✅ PDFs attached: {stats['pdf_attached']}\n"
            f"• ❌ Attachment failed: {stats['pdf_failed']}\n"
        )

        if stats["pdf_attached"] > 0:
            report += f"\n🎉 Successfully attached {stats['pdf_attached']} PDF(s)!"
        elif stats["has_attachment"] == stats["scanned"]:
            report += "\n✨ All scanned items already have PDFs!"
        else:
            report += "\n💡 Tip: PDFs are only available for open access papers (arXiv, bioRxiv, some DOIs)"

        await status_msg.edit(content=report)
        logger.info(f"PDF attachment scan complete: {stats}")

    except Exception as e:
        logger.error(f"Error in attach_pdfs command: {e}")
        await interaction.followup.send(f"❌ Error during PDF attachment: {str(e)}")


# ============================================================================
# Run Bot
# ============================================================================

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
