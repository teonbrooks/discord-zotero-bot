import os
import re
import logging
from typing import List, Dict, Set, Tuple, Optional
import asyncio
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from pyzotero import zotero
import httpx

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
# Helper Functions
# ============================================================================

def strip_html_tags(text: str) -> str:
    """
    Remove HTML/XML tags from text, keeping only the text content.
    Specifically removes <jats:title> and other title tags completely.
    """
    if not text:
        return ''
    
    # First, remove title tags and their content completely
    # Matches <jats:title>...</jats:title>, <title>...</title>, etc.
    clean_text = re.sub(r'<[^>]*title[^>]*>.*?</[^>]*title[^>]*>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove remaining XML/HTML tags, replacing with a space
    # This removes tags like <jats:p>, </jats:p>, <p>, etc.
    clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
    
    # Clean up extra whitespace (multiple spaces become one)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Remove leading/trailing whitespace
    clean_text = clean_text.strip()
    
    return clean_text


def get_pdf_url(identifier_type: str, identifier: str, metadata: Optional[Dict] = None) -> Optional[str]:
    """
    Get PDF URL for a given identifier type and identifier.
    Returns None if PDF URL cannot be determined.
    """
    try:
        if identifier_type == 'arxiv':
            # arXiv PDFs are available at https://arxiv.org/pdf/{id}.pdf
            # Handle both old (e.g., 0704.0001) and new (e.g., 2404.05553) formats
            return f"https://arxiv.org/pdf/{identifier}.pdf"
        
        elif identifier_type == 'biorxiv':
            # bioRxiv DOI format: 10.1101/2023.05.15.540123
            # PDF URL: https://www.biorxiv.org/content/{doi}v1.full.pdf
            if identifier.startswith('10.1101/'):
                # Extract the numeric part after 10.1101/
                numeric_id = identifier.replace('10.1101/', '')
                # Try to get version from metadata, default to v1
                version = 'v1'
                if metadata and 'url' in metadata:
                    # Check if URL contains version info
                    version_match = re.search(r'(v\d+)', metadata['url'])
                    if version_match:
                        version = version_match.group(1)
                return f"https://www.biorxiv.org/content/10.1101/{numeric_id}{version}.full.pdf"
            return None
        
        elif identifier_type == 'doi':
            # For DOIs, check if there's an open access PDF link in CrossRef metadata
            # This is best-effort - not all papers have open access PDFs
            if metadata:
                # Check for links in CrossRef metadata
                links = metadata.get('link', [])
                for link in links:
                    if link.get('content-type') == 'application/pdf':
                        return link.get('URL')
            return None
        
        elif identifier_type == 'pubmed':
            # For PubMed, check if there's a PMC (PubMed Central) full-text PDF
            # This requires additional PMC ID lookup, which we'll skip for now
            # Could be enhanced in the future
            return None
        
        else:
            return None
    
    except Exception as e:
        logger.error(f"Error getting PDF URL for {identifier_type} {identifier}: {e}")
        return None


async def download_and_attach_pdf(item_key: str, pdf_url: str, filename: str) -> bool:
    """
    Download PDF from URL and attach it to a Zotero item.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info(f"Attempting to download PDF from: {pdf_url}")
        
        # Download PDF with timeout
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(pdf_url)
            
            if response.status_code == 200:
                pdf_content = response.content
                
                # Check if content looks like a PDF
                if not pdf_content.startswith(b'%PDF'):
                    logger.warning(f"Downloaded content doesn't appear to be a PDF")
                    return False
                
                logger.info(f"Successfully downloaded PDF ({len(pdf_content)} bytes)")
                
                # Attach PDF to Zotero item
                # pyzotero expects a file path or file-like object
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(pdf_content)
                    tmp_path = tmp_file.name
                
                try:
                    # Upload attachment to Zotero
                    zot.attachment_simple([tmp_path], item_key)
                    logger.info(f"Successfully attached PDF to Zotero item {item_key}")
                    return True
                except Exception as e:
                    logger.error(f"Error attaching PDF to Zotero: {e}")
                    return False
                finally:
                    # Clean up temporary file
                    import os as os_module
                    try:
                        os_module.unlink(tmp_path)
                    except:
                        pass
            else:
                logger.warning(f"Failed to download PDF: HTTP {response.status_code}")
                return False
    
    except httpx.TimeoutException:
        logger.warning(f"Timeout while downloading PDF from {pdf_url}")
        return False
    except Exception as e:
        logger.error(f"Error downloading and attaching PDF: {e}")
        return False


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
        # arXiv DOI format: 10.48550/arXiv.XXXX.XXXXX
        r'(?:doi\.org/)?10\.48550/arXiv\.(\d{4}\.\d{4,5}(?:v\d+)?)',
        # Standard arXiv URLs
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)',
        # Bare arXiv ID
        r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b',
    ]
    
    for pattern in arxiv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_biorxiv_doi(text: str) -> Optional[str]:
    """Extract bioRxiv DOI from text or URL."""
    # Match bioRxiv patterns
    # bioRxiv DOIs are typically: 10.1101/YYYY.MM.DD.XXXXXX
    biorxiv_patterns = [
        r'biorxiv\.org/content/(10\.1101/\d{4}\.\d{2}\.\d{2}\.\d+(?:v\d+)?)',
        r'doi\.org/(10\.1101/\d{4}\.\d{2}\.\d{2}\.\d+)',
        r'\b(10\.1101/\d{4}\.\d{2}\.\d{2}\.\d+(?:v\d+)?)\b',
    ]
    
    for pattern in biorxiv_patterns:
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
    Returns (type, identifier) where type is one of: 'doi', 'arxiv', 'biorxiv', 'pubmed', 'pdf', 'generic'
    """
    logger.debug(f"Categorizing link: {url}")
    
    # Check for arXiv first (including arXiv DOIs like 10.48550/arXiv.*)
    arxiv_id = extract_arxiv_id(url)
    if arxiv_id:
        logger.info(f"Detected arXiv link with ID: {arxiv_id}")
        return ('arxiv', arxiv_id)
    
    # Check for bioRxiv (before general DOI check, as bioRxiv uses DOIs)
    biorxiv_doi = extract_biorxiv_doi(url)
    if biorxiv_doi:
        logger.info(f"Detected bioRxiv link with DOI: {biorxiv_doi}")
        return ('biorxiv', biorxiv_doi)
    
    # Check for general DOI
    doi = extract_doi(url)
    if doi:
        logger.info(f"Detected DOI link: {doi}")
        return ('doi', doi)
    
    # Check for PubMed
    pubmed_id = extract_pubmed_id(url)
    if pubmed_id:
        logger.info(f"Detected PubMed link with ID: {pubmed_id}")
        return ('pubmed', pubmed_id)
    
    # Check for PDF
    if is_pdf_url(url):
        logger.info(f"Detected PDF link: {url}")
        return ('pdf', url)
    
    # Generic URL
    logger.info(f"Treating as generic URL: {url}")
    return ('generic', url)


# ============================================================================
# Metadata Fetching Functions
# ============================================================================

async def fetch_crossref_metadata(doi: str) -> Optional[Dict]:
    """Fetch metadata from CrossRef API for a given DOI."""
    try:
        url = f"https://api.crossref.org/works/{doi}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('message', {})
            else:
                logger.warning(f"CrossRef API returned status {response.status_code} for DOI: {doi}")
                return None
    except Exception as e:
        logger.error(f"Error fetching CrossRef metadata for {doi}: {e}")
        return None


async def fetch_arxiv_metadata(arxiv_id: str) -> Optional[Dict]:
    """Fetch metadata from arXiv API for a given arXiv ID."""
    try:
        # Remove version suffix if present
        base_id = arxiv_id.split('v')[0]
        url = f"https://export.arxiv.org/api/query?id_list={base_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                # Parse XML response
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entry = root.find('atom:entry', ns)
                
                if entry is not None:
                    metadata = {}
                    
                    # Title
                    title_elem = entry.find('atom:title', ns)
                    if title_elem is not None:
                        metadata['title'] = title_elem.text.strip()
                    
                    # Authors
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    metadata['authors'] = authors
                    
                    # Abstract
                    summary_elem = entry.find('atom:summary', ns)
                    if summary_elem is not None:
                        metadata['abstract'] = summary_elem.text.strip()
                    
                    # Published date
                    published_elem = entry.find('atom:published', ns)
                    if published_elem is not None:
                        metadata['published'] = published_elem.text.strip()
                    
                    # Categories
                    categories = []
                    for category in entry.findall('atom:category', ns):
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    metadata['categories'] = categories
                    
                    # DOI (if available)
                    doi_elem = entry.find('atom:doi', ns)
                    if doi_elem is not None:
                        metadata['doi'] = doi_elem.text.strip()
                    
                    # URL
                    metadata['url'] = f"https://arxiv.org/abs/{arxiv_id}"
                    
                    logger.info(f"Successfully parsed arXiv metadata for {arxiv_id}")
                    return metadata
                else:
                    logger.warning(f"No entry found in arXiv API response for ID: {arxiv_id}")
                    return None
            else:
                logger.warning(f"arXiv API returned status {response.status_code} for ID: {arxiv_id}")
                return None
    except Exception as e:
        logger.error(f"Error fetching arXiv metadata for {arxiv_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def fetch_biorxiv_metadata(doi: str) -> Optional[Dict]:
    """Fetch metadata from bioRxiv API for a given bioRxiv DOI."""
    try:
        # Remove version suffix if present (e.g., v1, v2)
        base_doi = re.sub(r'v\d+$', '', doi)
        
        # bioRxiv API endpoint
        url = f"https://api.biorxiv.org/details/biorxiv/{base_doi}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # bioRxiv API returns data in a 'collection' array
                collection = data.get('collection', [])
                if collection and len(collection) > 0:
                    item = collection[0]
                    metadata = {}
                    
                    # Title
                    metadata['title'] = item.get('title', '')
                    
                    # Authors (formatted as "LastName, FirstName")
                    authors_str = item.get('authors', '')
                    if authors_str:
                        # Split by semicolon or comma depending on format
                        if ';' in authors_str:
                            authors_list = [a.strip() for a in authors_str.split(';')]
                        else:
                            # Try to intelligently split by commas (tricky with "Last, First" format)
                            authors_list = [authors_str]
                        metadata['authors'] = authors_list
                    
                    # Abstract
                    metadata['abstract'] = item.get('abstract', '')
                    
                    # DOI
                    metadata['doi'] = item.get('doi', doi)
                    
                    # Date
                    metadata['date'] = item.get('date', '')
                    
                    # Category/Subject
                    metadata['category'] = item.get('category', '')
                    
                    # URL
                    metadata['url'] = f"https://www.biorxiv.org/content/{doi}"
                    
                    # Version
                    metadata['version'] = item.get('version', '')
                    
                    return metadata
            
            logger.warning(f"bioRxiv API returned status {response.status_code} for DOI: {doi}")
            return None
    except Exception as e:
        logger.error(f"Error fetching bioRxiv metadata for {doi}: {e}")
        return None


async def fetch_pubmed_metadata(pmid: str) -> Optional[Dict]:
    """Fetch metadata from PubMed API for a given PMID."""
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {}).get(pmid, {})
                
                if result and 'error' not in result:
                    metadata = {}
                    
                    # Title
                    metadata['title'] = result.get('title', '')
                    
                    # Authors
                    authors = []
                    for author in result.get('authors', []):
                        name = author.get('name', '')
                        if name:
                            authors.append(name)
                    metadata['authors'] = authors
                    
                    # Journal
                    metadata['journal'] = result.get('fulljournalname', result.get('source', ''))
                    
                    # Publication date
                    pub_date = result.get('pubdate', '')
                    metadata['date'] = pub_date
                    
                    # DOI
                    for articleid in result.get('articleids', []):
                        if articleid.get('idtype') == 'doi':
                            metadata['doi'] = articleid.get('value')
                            break
                    
                    # Volume, Issue, Pages
                    metadata['volume'] = result.get('volume', '')
                    metadata['issue'] = result.get('issue', '')
                    metadata['pages'] = result.get('pages', '')
                    
                    # URL
                    metadata['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    
                    return metadata
            
            logger.warning(f"PubMed API returned status {response.status_code} for PMID: {pmid}")
            return None
    except Exception as e:
        logger.error(f"Error fetching PubMed metadata for {pmid}: {e}")
        return None


# ============================================================================
# Zotero Integration Functions
# ============================================================================

def search_zotero_by_doi(doi: str) -> bool:
    """Check if item with DOI already exists in Zotero library."""
    try:
        # Normalize DOI
        normalized_doi = doi.strip().lower()
        
        # First, try searching with the DOI string - check both full DOI and just the suffix
        search_terms = [doi, normalized_doi]
        
        # Also try just the suffix (after "10.")
        if '/' in doi:
            suffix = doi.split('/', 1)[1]
            search_terms.append(suffix)
        
        all_results = []
        for term in search_terms:
            try:
                results = zot.items(q=term, limit=100)
                all_results.extend(results)
            except Exception:
                continue
        
        # Check all results
        seen_keys = set()
        for item in all_results:
            # Skip duplicates from multiple searches
            item_key = item.get('key')
            if item_key in seen_keys:
                continue
            seen_keys.add(item_key)
            
            item_data = item.get('data', {})
            item_doi = item_data.get('DOI', '').strip().lower()
            if item_doi and item_doi == normalized_doi:
                logger.info(f"Found existing item with DOI: {doi}")
                return True
            
            # Also check extra field where DOI might be stored
            extra = item_data.get('extra', '')
            if extra and normalized_doi in extra.lower():
                logger.info(f"Found existing item with DOI in extra field: {doi}")
                return True
        
        # If text search didn't find it, check recent items as fallback
        # This handles cases where the text search doesn't index DOI field well
        try:
            recent_items = zot.top(limit=100)
            for item in recent_items:
                item_data = item.get('data', {})
                item_doi = item_data.get('DOI', '').strip().lower()
                if item_doi and item_doi == normalized_doi:
                    logger.info(f"Found existing item with DOI in recent items: {doi}")
                    return True
        except Exception:
            pass
        
        return False
    except Exception as e:
        logger.error(f"Error searching Zotero by DOI: {e}")
        return False


def search_zotero_by_url(url: str) -> bool:
    """Check if item with URL already exists in Zotero library."""
    try:
        # Normalize URL (remove trailing slashes, convert to lowercase for comparison)
        normalized_url = url.strip().rstrip('/').lower()
        
        # Also check common URL variations
        url_variations = [normalized_url]
        
        # Add http/https variations
        if normalized_url.startswith('https://'):
            url_variations.append(normalized_url.replace('https://', 'http://'))
        elif normalized_url.startswith('http://'):
            url_variations.append(normalized_url.replace('http://', 'https://'))
        
        # Extract domain for searching
        domain_match = re.search(r'https?://([^/]+)', url)
        search_terms = []
        if domain_match:
            search_terms.append(domain_match.group(1))
        
        # Add the full URL
        search_terms.append(url)
        
        # Search with multiple terms
        all_results = []
        for term in search_terms:
            try:
                results = zot.items(q=term, limit=100)
                all_results.extend(results)
            except Exception:
                continue
        
        # Check all results
        seen_keys = set()
        for item in all_results:
            # Skip duplicates from multiple searches
            item_key = item.get('key')
            if item_key in seen_keys:
                continue
            seen_keys.add(item_key)
            
            item_data = item.get('data', {})
            item_url = item_data.get('url', '').strip().rstrip('/').lower()
            
            if item_url and item_url in url_variations:
                logger.info(f"Found existing item with URL: {url}")
                return True
            
            # Check if URL contains the DOI path
            if 'doi.org' in normalized_url:
                doi_match = re.search(r'doi\.org/(10\.\S+)', normalized_url)
                if doi_match:
                    doi = doi_match.group(1)
                    item_doi = item_data.get('DOI', '').strip().lower()
                    if item_doi and item_doi == doi.lower():
                        logger.info(f"Found existing item with matching DOI from URL: {url}")
                        return True
        
        # Check recent items as fallback
        try:
            recent_items = zot.top(limit=100)
            for item in recent_items:
                item_data = item.get('data', {})
                item_url = item_data.get('url', '').strip().rstrip('/').lower()
                
                if item_url and item_url in url_variations:
                    logger.info(f"Found existing item with URL in recent items: {url}")
                    return True
        except Exception:
            pass
        
        return False
    except Exception as e:
        logger.error(f"Error searching Zotero by URL: {e}")
        return False


def search_zotero_by_title(title: str) -> bool:
    """Check if item with similar title already exists in Zotero library."""
    try:
        if not title or len(title) < 10:
            return False
        
        # Normalize title for comparison
        normalized_title = ' '.join(title.lower().split())
        
        results = zot.items(q=title, limit=20)
        for item in results:
            item_title = item.get('data', {}).get('title', '').lower()
            item_title_normalized = ' '.join(item_title.split())
            
            # Check for exact or very similar match
            if item_title_normalized == normalized_title:
                logger.info(f"Found existing item with matching title: {title[:50]}...")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error searching Zotero by title: {e}")
        return False


def check_duplicate_comprehensive(doi: Optional[str] = None, url: Optional[str] = None, title: Optional[str] = None) -> bool:
    """
    Comprehensive duplicate check using multiple fields.
    Returns True if a duplicate is found.
    """
    logger.debug(f"Comprehensive duplicate check - DOI: {doi}, URL: {url}, Title: {title[:50] if title else None}...")
    
    # Check DOI first (most reliable)
    if doi:
        logger.debug(f"Checking DOI: {doi}")
        if search_zotero_by_doi(doi):
            logger.info(f"Duplicate found via DOI: {doi}")
            return True
    
    # Check URL
    if url:
        logger.debug(f"Checking URL: {url}")
        if search_zotero_by_url(url):
            logger.info(f"Duplicate found via URL: {url}")
            return True
    
    # Check title as last resort
    if title:
        logger.debug(f"Checking title: {title[:50]}...")
        if search_zotero_by_title(title):
            logger.info(f"Duplicate found via title: {title[:50]}...")
            return True
    
    logger.debug("No duplicate found")
    return False


async def add_to_zotero_by_identifier(identifier_type: str, identifier: str, tags: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Add item to Zotero by identifier (DOI, arXiv ID, PMID) with full metadata.
    Returns (success, message)
    """
    try:
        if tags is None:
            tags = []
        
        metadata = None
        
        # Fetch metadata based on identifier type
        if identifier_type == 'doi':
            # Check for duplicate DOI first
            logger.info(f"Checking for duplicate DOI: {identifier}")
            if check_duplicate_comprehensive(doi=identifier):
                logger.info(f"Duplicate found for DOI: {identifier}")
                return (False, "duplicate")
            logger.info(f"No duplicate found, fetching metadata for DOI: {identifier}")
            metadata = await fetch_crossref_metadata(identifier)
            if metadata:
                # Create journal article template
                template = zot.item_template('journalArticle')
                
                # Populate with CrossRef metadata
                template['DOI'] = identifier
                template['title'] = metadata.get('title', [''])[0] if isinstance(metadata.get('title'), list) else metadata.get('title', '')
                
                # Authors
                if 'author' in metadata:
                    creators = []
                    for author in metadata['author']:
                        creator = {
                            'creatorType': 'author',
                            'firstName': author.get('given', ''),
                            'lastName': author.get('family', '')
                        }
                        creators.append(creator)
                    template['creators'] = creators
                
                # Journal info
                container_title = metadata.get('container-title', [])
                if container_title:
                    template['publicationTitle'] = container_title[0] if isinstance(container_title, list) else container_title
                
                # Volume, Issue, Pages
                template['volume'] = metadata.get('volume', '')
                template['issue'] = metadata.get('issue', '')
                template['pages'] = metadata.get('page', '')
                
                # Date
                published = metadata.get('published', {}) or metadata.get('published-print', {})
                if published and 'date-parts' in published:
                    date_parts = published['date-parts'][0]
                    if len(date_parts) >= 1:
                        template['date'] = '-'.join(map(str, date_parts))
                
                # Abstract (clean XML/HTML tags)
                raw_abstract = metadata.get('abstract', '')
                template['abstractNote'] = strip_html_tags(raw_abstract)
                
                # URL
                template['url'] = metadata.get('URL', f"https://doi.org/{identifier}")
                
                # Tags
                template['tags'] = [{'tag': tag} for tag in tags]
                
                try:
                    items = zot.create_items([template])
                    logger.info(f"Added item with DOI and metadata: {identifier}")
                    
                    # Try to attach PDF if available
                    if items and 'successful' in items and items['successful']:
                        item_key = items['successful']['0']['key']
                        pdf_url = get_pdf_url('doi', identifier, metadata)
                        if pdf_url:
                            logger.info(f"Found PDF URL for DOI, attempting to attach")
                            await download_and_attach_pdf(item_key, pdf_url, f"{identifier}.pdf")
                        else:
                            logger.info(f"No open access PDF available for DOI: {identifier}")
                    
                    return (True, "success")
                except Exception as e:
                    logger.error(f"Error creating Zotero item: {e}")
                    return (False, str(e))
            else:
                logger.warning(f"Could not fetch metadata for DOI: {identifier}")
                return (False, "metadata_fetch_failed")
        
        elif identifier_type == 'arxiv':
            logger.info(f"Processing arXiv paper with ID: {identifier}")
            metadata = await fetch_arxiv_metadata(identifier)
            if metadata:
                logger.info(f"Successfully fetched arXiv metadata for: {identifier}")
                # Comprehensive duplicate check
                if check_duplicate_comprehensive(
                    doi=metadata.get('doi'),
                    url=metadata.get('url'),
                    title=metadata.get('title')
                ):
                    logger.info(f"arXiv paper {identifier} is a duplicate")
                    return (False, "duplicate")
                
                # Create preprint template
                template = zot.item_template('preprint')
                
                # Populate with arXiv metadata
                template['title'] = metadata.get('title', '')
                template['abstractNote'] = strip_html_tags(metadata.get('abstract', ''))
                template['url'] = metadata['url']
                template['repository'] = 'arXiv'
                template['archiveID'] = identifier
                
                # Authors
                if 'authors' in metadata:
                    creators = []
                    for author_name in metadata['authors']:
                        # Split name (basic approach)
                        parts = author_name.rsplit(' ', 1)
                        creator = {
                            'creatorType': 'author',
                            'firstName': parts[0] if len(parts) > 1 else '',
                            'lastName': parts[-1]
                        }
                        creators.append(creator)
                    template['creators'] = creators
                
                # Date
                if 'published' in metadata:
                    template['date'] = metadata['published'].split('T')[0]
                
                # DOI if available
                if 'doi' in metadata:
                    template['DOI'] = metadata['doi']
                
                # Tags
                template['tags'] = [{'tag': tag} for tag in tags]
                
                try:
                    items = zot.create_items([template])
                    logger.info(f"Added arXiv item with metadata: {identifier}")
                    
                    # Attach PDF (arXiv PDFs are freely available)
                    if items and 'successful' in items and items['successful']:
                        item_key = items['successful']['0']['key']
                        pdf_url = get_pdf_url('arxiv', identifier, metadata)
                        if pdf_url:
                            logger.info(f"Attaching arXiv PDF from: {pdf_url}")
                            await download_and_attach_pdf(item_key, pdf_url, f"arxiv_{identifier}.pdf")
                    
                    return (True, "success")
                except Exception as e:
                    logger.error(f"Error creating Zotero item: {e}")
                    return (False, str(e))
            else:
                logger.warning(f"Could not fetch metadata for arXiv: {identifier}")
                return (False, "metadata_fetch_failed")
        
        elif identifier_type == 'biorxiv':
            metadata = await fetch_biorxiv_metadata(identifier)
            if metadata:
                # Comprehensive duplicate check
                if check_duplicate_comprehensive(
                    doi=metadata.get('doi'),
                    url=metadata.get('url'),
                    title=metadata.get('title')
                ):
                    return (False, "duplicate")
                
                # Create preprint template
                template = zot.item_template('preprint')
                
                # Populate with bioRxiv metadata
                template['title'] = metadata.get('title', '')
                template['abstractNote'] = strip_html_tags(metadata.get('abstract', ''))
                template['url'] = metadata['url']
                template['repository'] = 'bioRxiv'
                template['archiveID'] = identifier
                
                # DOI
                if 'doi' in metadata:
                    template['DOI'] = metadata['doi']
                
                # Authors
                if 'authors' in metadata:
                    creators = []
                    for author_name in metadata['authors']:
                        # bioRxiv format can be "Last, First" or "First Last"
                        if ',' in author_name:
                            # Format: "Last, First"
                            parts = author_name.split(',', 1)
                            creator = {
                                'creatorType': 'author',
                                'lastName': parts[0].strip(),
                                'firstName': parts[1].strip() if len(parts) > 1 else ''
                            }
                        else:
                            # Format: "First Last" or just name
                            parts = author_name.rsplit(' ', 1)
                            creator = {
                                'creatorType': 'author',
                                'firstName': parts[0] if len(parts) > 1 else '',
                                'lastName': parts[-1]
                            }
                        creators.append(creator)
                    template['creators'] = creators
                
                # Date
                if 'date' in metadata:
                    template['date'] = metadata['date']
                
                # Tags
                template['tags'] = [{'tag': tag} for tag in tags]
                
                try:
                    items = zot.create_items([template])
                    logger.info(f"Added bioRxiv item with metadata: {identifier}")
                    
                    # Attach PDF (bioRxiv PDFs are freely available)
                    if items and 'successful' in items and items['successful']:
                        item_key = items['successful']['0']['key']
                        pdf_url = get_pdf_url('biorxiv', identifier, metadata)
                        if pdf_url:
                            logger.info(f"Attaching bioRxiv PDF from: {pdf_url}")
                            await download_and_attach_pdf(item_key, pdf_url, f"biorxiv_{identifier.replace('/', '_')}.pdf")
                    
                    return (True, "success")
                except Exception as e:
                    logger.error(f"Error creating Zotero item: {e}")
                    return (False, str(e))
            else:
                logger.warning(f"Could not fetch metadata for bioRxiv: {identifier}")
                return (False, "metadata_fetch_failed")
        
        elif identifier_type == 'pubmed':
            metadata = await fetch_pubmed_metadata(identifier)
            if metadata:
                # Comprehensive duplicate check
                if check_duplicate_comprehensive(
                    doi=metadata.get('doi'),
                    url=metadata.get('url'),
                    title=metadata.get('title')
                ):
                    return (False, "duplicate")
                
                # Create journal article template
                template = zot.item_template('journalArticle')
                
                # Populate with PubMed metadata
                template['title'] = metadata.get('title', '')
                template['publicationTitle'] = metadata.get('journal', '')
                template['volume'] = metadata.get('volume', '')
                template['issue'] = metadata.get('issue', '')
                template['pages'] = metadata.get('pages', '')
                template['date'] = metadata.get('date', '')
                template['url'] = metadata['url']
                
                # DOI if available
                if 'doi' in metadata:
                    template['DOI'] = metadata['doi']
                
                # Authors
                if 'authors' in metadata:
                    creators = []
                    for author_name in metadata['authors']:
                        # Parse name (format: "Last FM")
                        parts = author_name.split(' ', 1)
                        creator = {
                            'creatorType': 'author',
                            'lastName': parts[0],
                            'firstName': parts[1] if len(parts) > 1 else ''
                        }
                        creators.append(creator)
                    template['creators'] = creators
                
                # Tags
                template['tags'] = [{'tag': tag} for tag in tags]
                
                try:
                    items = zot.create_items([template])
                    logger.info(f"Added PubMed item with metadata: {identifier}")
                    return (True, "success")
                except Exception as e:
                    logger.error(f"Error creating Zotero item: {e}")
                    return (False, str(e))
            else:
                logger.warning(f"Could not fetch metadata for PubMed: {identifier}")
                return (False, "metadata_fetch_failed")
        
        return (False, "unsupported_identifier_type")
        
    except Exception as e:
        logger.error(f"Error adding item by identifier: {e}")
        return (False, str(e))


async def fetch_webpage_metadata(url: str) -> Optional[Dict]:
    """Attempt to fetch basic metadata from a webpage."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ZoteroBot/1.0)'
            })
            
            if response.status_code == 200:
                html_content = response.text
                metadata = {}
                
                # Extract title from <title> tag or meta tags
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
                if title_match:
                    metadata['title'] = title_match.group(1).strip()
                
                # Try to extract DOI from meta tags or content
                doi_patterns = [
                    r'<meta[^>]+name=["\']citation_doi["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_doi',
                ]
                for pattern in doi_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        metadata['doi'] = match.group(1)
                        break
                
                # Extract publication date
                date_patterns = [
                    r'<meta[^>]+name=["\']citation_publication_date["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_publication_date',
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        metadata['date'] = match.group(1)
                        break
                
                # Extract journal name
                journal_patterns = [
                    r'<meta[^>]+name=["\']citation_journal_title["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_journal_title',
                ]
                for pattern in journal_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        metadata['journal'] = match.group(1)
                        break
                
                # Extract authors
                author_patterns = [
                    r'<meta[^>]+name=["\']citation_author["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_author',
                ]
                authors = []
                for match in re.finditer(author_patterns[0], html_content, re.IGNORECASE):
                    authors.append(match.group(1))
                if not authors:
                    for match in re.finditer(author_patterns[1], html_content, re.IGNORECASE):
                        authors.append(match.group(1))
                if authors:
                    metadata['authors'] = authors
                
                return metadata if metadata else None
            
            return None
    except Exception as e:
        logger.error(f"Error fetching webpage metadata: {e}")
        return None


async def add_to_zotero_by_url(url: str, tags: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Add item to Zotero by URL, attempting to extract metadata.
    Returns (success, message)
    """
    try:
        if tags is None:
            tags = []
        
        # Try to fetch metadata from the webpage first
        metadata = await fetch_webpage_metadata(url)
        
        # Comprehensive duplicate check with all available information
        if check_duplicate_comprehensive(
            doi=metadata.get('doi') if metadata else None,
            url=url,
            title=metadata.get('title') if metadata else None
        ):
            return (False, "duplicate")
        
        # If we found a DOI in the metadata, use that for richer data
        if metadata and 'doi' in metadata:
            doi = metadata['doi']
            logger.info(f"Found DOI {doi} in webpage, using CrossRef metadata")
            # Note: We already checked for duplicates above, so pass through
            return await add_to_zotero_by_identifier('doi', doi, tags=tags)
        
        # Create item with available metadata
        if metadata and metadata.get('journal'):
            # Looks like a journal article
            template = zot.item_template('journalArticle')
            template['title'] = metadata.get('title', url)
            template['publicationTitle'] = metadata.get('journal', '')
            template['date'] = metadata.get('date', '')
            template['url'] = url
            
            # Authors
            if 'authors' in metadata:
                creators = []
                for author_name in metadata['authors']:
                    # Try to split first/last name
                    parts = author_name.rsplit(' ', 1)
                    creator = {
                        'creatorType': 'author',
                        'firstName': parts[0] if len(parts) > 1 else '',
                        'lastName': parts[-1]
                    }
                    creators.append(creator)
                template['creators'] = creators
        else:
            # Fallback to webpage item
            template = zot.item_template('webpage')
            template['url'] = url
            template['title'] = metadata.get('title', url) if metadata else url
            
            if metadata and 'date' in metadata:
                template['accessDate'] = metadata['date']
        
        # Add extra note
        template['extra'] = "Added via Discord Zotero Bot"
        
        # Tags
        template['tags'] = [{'tag': tag} for tag in tags]
        
        try:
            items = zot.create_items([template])
            logger.info(f"Added item from URL with metadata: {url}")
            return (True, "success")
        except Exception as e:
            logger.error(f"Error creating Zotero item: {e}")
            return (False, str(e))
        
    except Exception as e:
        logger.error(f"Error adding item by URL: {e}")
        return (False, str(e))


async def process_link(url: str, channel_name: Optional[str] = None) -> Tuple[bool, bool]:
    """
    Process a single link and add to Zotero if not duplicate.
    Returns (was_added, is_duplicate)
    """
    link_type, identifier = categorize_link(url)
    
    logger.info(f"Processing link: {url} (type: {link_type})")
    
    # Prepare tags
    tags = ['discord-zotero-bot']
    if channel_name:
        tags.append(channel_name)
    
    try:
        if link_type in ['doi', 'arxiv', 'biorxiv', 'pubmed']:
            success, message = await add_to_zotero_by_identifier(link_type, identifier, tags=tags)
        else:  # pdf or generic
            success, message = await add_to_zotero_by_url(url, tags=tags)
        
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
    
    # Get channel name for tagging
    channel_name = message.channel.name if hasattr(message.channel, 'name') else None
    
    # Process each URL
    processed_urls: Set[str] = set()
    
    for url in urls:
        if url in processed_urls:
            continue
        processed_urls.add(url)
        
        try:
            was_added, is_duplicate = await process_link(url, channel_name=channel_name)
            
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
