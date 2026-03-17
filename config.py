import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ZOTERO_TOKEN = os.getenv("ZOTERO_TOKEN")
ZOTERO_GROUP_ID = os.getenv("ZOTERO_GROUP_ID")
PAPERS_CATEGORY_NAME = os.getenv("PAPERS_CATEGORY_NAME", "papers")
MAX_MESSAGES_PER_CHANNEL = int(os.getenv("MAX_MESSAGES_PER_CHANNEL", "100"))

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")
if not ZOTERO_TOKEN:
    raise ValueError("ZOTERO_TOKEN environment variable is required")
if not ZOTERO_GROUP_ID:
    raise ValueError("ZOTERO_GROUP_ID environment variable is required")

SUCCESS_EMOJI = "🤖"
DUPLICATE_EMOJI = "✅"
ERROR_EMOJI = "❌"
