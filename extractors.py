import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def strip_html_tags(text: str) -> str:
    """
    Remove HTML/XML tags from text, keeping only the text content.
    Specifically removes <jats:title> and other title tags completely.
    """
    if not text:
        return ""

    # First, remove title tags and their content completely
    # Matches <jats:title>...</jats:title>, <title>...</title>, etc.
    clean_text = re.sub(r"<[^>]*title[^>]*>.*?</[^>]*title[^>]*>", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove remaining XML/HTML tags, replacing with a space
    clean_text = re.sub(r"<[^>]+>", " ", clean_text)

    # Clean up extra whitespace
    clean_text = re.sub(r"\s+", " ", clean_text)

    return clean_text.strip()


def extract_urls_from_message(content: str) -> List[str]:
    """Extract all URLs from message content."""
    url_pattern = r'https?://[^\s<>"\'\)]+(?:\([^\s<>"\'\)]*\))*[^\s<>"\'\)\.,;:]?'
    return re.findall(url_pattern, content)


def extract_doi(text: str) -> Optional[str]:
    """Extract DOI from text or URL."""
    doi_patterns = [
        r"(?:https?://)?(?:dx\.)?doi\.org/(10\.\S+)",
        r"\b(10\.\d{4,}(?:\.\d+)*(?:/|%2F)[^\s]+)",
    ]

    for pattern in doi_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            doi = match.group(1)
            doi = doi.rstrip(".,;:)")
            return doi
    return None


def extract_arxiv_id(text: str) -> Optional[str]:
    """Extract arXiv ID from text or URL."""
    arxiv_patterns = [
        # arXiv DOI format: 10.48550/arXiv.XXXX.XXXXX
        r"(?:doi\.org/)?10\.48550/arXiv\.(\d{4}\.\d{4,5}(?:v\d+)?)",
        # Standard arXiv URLs
        r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)",
        # Bare arXiv ID
        r"\b(\d{4}\.\d{4,5}(?:v\d+)?)\b",
    ]

    for pattern in arxiv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_biorxiv_doi(text: str) -> Optional[str]:
    """Extract bioRxiv DOI from text or URL."""
    biorxiv_patterns = [
        r"biorxiv\.org/content/(10\.1101/\d{4}\.\d{2}\.\d{2}\.\d+(?:v\d+)?)",
        r"doi\.org/(10\.1101/\d{4}\.\d{2}\.\d{2}\.\d+)",
        r"\b(10\.1101/\d{4}\.\d{2}\.\d{2}\.\d+(?:v\d+)?)\b",
    ]

    for pattern in biorxiv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_pubmed_id(text: str) -> Optional[str]:
    """Extract PubMed ID from text or URL."""
    pubmed_patterns = [
        r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)",
        r"ncbi\.nlm\.nih\.gov/pubmed/(\d+)",
        r"\bPMID:?\s*(\d+)\b",
    ]

    for pattern in pubmed_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def is_pdf_url(url: str) -> bool:
    """Check if URL points to a PDF file."""
    return url.lower().endswith(".pdf") or ".pdf?" in url.lower()


def categorize_link(url: str) -> Tuple[str, Optional[str]]:
    """
    Categorize a link and extract its identifier.
    Returns (type, identifier) where type is one of:
    'doi', 'arxiv', 'biorxiv', 'pubmed', 'pdf', 'generic'
    """
    logger.debug(f"Categorizing link: {url}")

    # arXiv — checked first, including arXiv DOIs (10.48550/arXiv.*)
    arxiv_id = extract_arxiv_id(url)
    if arxiv_id:
        logger.info(f"Detected arXiv link with ID: {arxiv_id}")
        return ("arxiv", arxiv_id)

    # bioRxiv — before general DOI check, as bioRxiv uses DOIs
    biorxiv_doi = extract_biorxiv_doi(url)
    if biorxiv_doi:
        logger.info(f"Detected bioRxiv link with DOI: {biorxiv_doi}")
        return ("biorxiv", biorxiv_doi)

    # General DOI
    doi = extract_doi(url)
    if doi:
        logger.info(f"Detected DOI link: {doi}")
        return ("doi", doi)

    # PubMed
    pubmed_id = extract_pubmed_id(url)
    if pubmed_id:
        logger.info(f"Detected PubMed link with ID: {pubmed_id}")
        return ("pubmed", pubmed_id)

    # Direct PDF link
    if is_pdf_url(url):
        logger.info(f"Detected PDF link: {url}")
        return ("pdf", url)

    logger.info(f"Treating as generic URL: {url}")
    return ("generic", url)
