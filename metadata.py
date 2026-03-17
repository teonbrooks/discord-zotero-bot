import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)


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
        base_id = arxiv_id.split('v')[0]
        url = f"https://export.arxiv.org/api/query?id_list={base_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entry = root.find('atom:entry', ns)

                if entry is not None:
                    metadata = {}

                    title_elem = entry.find('atom:title', ns)
                    if title_elem is not None:
                        metadata['title'] = title_elem.text.strip()

                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    metadata['authors'] = authors

                    summary_elem = entry.find('atom:summary', ns)
                    if summary_elem is not None:
                        metadata['abstract'] = summary_elem.text.strip()

                    published_elem = entry.find('atom:published', ns)
                    if published_elem is not None:
                        metadata['published'] = published_elem.text.strip()

                    categories = []
                    for category in entry.findall('atom:category', ns):
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    metadata['categories'] = categories

                    doi_elem = entry.find('atom:doi', ns)
                    if doi_elem is not None:
                        metadata['doi'] = doi_elem.text.strip()

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
        base_doi = re.sub(r'v\d+$', '', doi)
        url = f"https://api.biorxiv.org/details/biorxiv/{base_doi}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                collection = data.get('collection', [])
                if collection and len(collection) > 0:
                    item = collection[0]
                    metadata = {}

                    metadata['title'] = item.get('title', '')

                    authors_str = item.get('authors', '')
                    if authors_str:
                        if ';' in authors_str:
                            authors_list = [a.strip() for a in authors_str.split(';')]
                        else:
                            authors_list = [authors_str]
                        metadata['authors'] = authors_list

                    metadata['abstract'] = item.get('abstract', '')
                    metadata['doi'] = item.get('doi', doi)
                    metadata['date'] = item.get('date', '')
                    metadata['category'] = item.get('category', '')
                    metadata['url'] = f"https://www.biorxiv.org/content/{doi}"
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

                    metadata['title'] = result.get('title', '')

                    authors = []
                    for author in result.get('authors', []):
                        name = author.get('name', '')
                        if name:
                            authors.append(name)
                    metadata['authors'] = authors

                    metadata['journal'] = result.get('fulljournalname', result.get('source', ''))
                    metadata['date'] = result.get('pubdate', '')

                    for articleid in result.get('articleids', []):
                        if articleid.get('idtype') == 'doi':
                            metadata['doi'] = articleid.get('value')
                            break

                    metadata['volume'] = result.get('volume', '')
                    metadata['issue'] = result.get('issue', '')
                    metadata['pages'] = result.get('pages', '')
                    metadata['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                    return metadata

            logger.warning(f"PubMed API returned status {response.status_code} for PMID: {pmid}")
            return None
    except Exception as e:
        logger.error(f"Error fetching PubMed metadata for {pmid}: {e}")
        return None


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

                title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
                if title_match:
                    metadata['title'] = title_match.group(1).strip()

                doi_patterns = [
                    r'<meta[^>]+name=["\']citation_doi["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_doi',
                ]
                for pattern in doi_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        metadata['doi'] = match.group(1)
                        break

                date_patterns = [
                    r'<meta[^>]+name=["\']citation_publication_date["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_publication_date',
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        metadata['date'] = match.group(1)
                        break

                journal_patterns = [
                    r'<meta[^>]+name=["\']citation_journal_title["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_journal_title',
                ]
                for pattern in journal_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        metadata['journal'] = match.group(1)
                        break

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
