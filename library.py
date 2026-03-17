import re
import logging
import tempfile
import shutil
import os
from typing import Dict, List, Set, Tuple, Optional

import httpx
from pyzotero import zotero

from config import ZOTERO_TOKEN, ZOTERO_GROUP_ID
from extractors import strip_html_tags, categorize_link
from metadata import (
    fetch_crossref_metadata,
    fetch_arxiv_metadata,
    fetch_biorxiv_metadata,
    fetch_pubmed_metadata,
    fetch_webpage_metadata,
)

logger = logging.getLogger(__name__)

zot = zotero.Zotero(ZOTERO_GROUP_ID, "group", ZOTERO_TOKEN)


# ============================================================================
# PDF Helpers
# ============================================================================


def get_pdf_url(identifier_type: str, identifier: str, metadata: Optional[Dict] = None) -> Optional[str]:
    """
    Get PDF URL for a given identifier type and identifier.
    Returns None if a PDF URL cannot be determined.
    """
    try:
        if identifier_type == "arxiv":
            return f"https://arxiv.org/pdf/{identifier}.pdf"

        elif identifier_type == "biorxiv":
            if identifier.startswith("10.1101/"):
                numeric_id = identifier.replace("10.1101/", "")
                version = "v1"
                if metadata and "url" in metadata:
                    version_match = re.search(r"(v\d+)", metadata["url"])
                    if version_match:
                        version = version_match.group(1)
                return f"https://www.biorxiv.org/content/10.1101/{numeric_id}{version}.full.pdf"
            return None

        elif identifier_type == "doi":
            if metadata:
                links = metadata.get("link", [])
                for link in links:
                    if link.get("content-type") == "application/pdf":
                        return link.get("URL")
            return None

        elif identifier_type == "pubmed":
            return None

        else:
            return None

    except Exception as e:
        logger.error(f"Error getting PDF URL for {identifier_type} {identifier}: {e}")
        return None


def _attach_linked_url(item_key: str, pdf_url: str, filename: str) -> bool:
    """Create a linked_url attachment pointing at pdf_url. Returns True on success."""
    url_template = zot.item_template("attachment", "linked_url")
    url_template["title"] = filename
    url_template["url"] = pdf_url
    url_template["contentType"] = "application/pdf"

    url_created = zot.create_items([url_template], parentid=item_key)

    if url_created.get("success"):
        logger.info(f"✓ PDF link attached for item {item_key}")
        return True
    else:
        logger.error(f"linked_url creation failed for item {item_key}: {url_created.get('failed', {})}")
        return False


def _delete_attachment_item(attachment_key: str) -> None:
    """Best-effort deletion of an orphaned attachment item."""
    try:
        zot.delete_item(zot.item(attachment_key))
        logger.debug(f"Deleted orphaned attachment item {attachment_key}")
    except Exception as e:
        logger.warning(f"Could not delete orphaned attachment {attachment_key}: {e}")


async def download_and_attach_pdf(item_key: str, pdf_url: str, filename: str) -> bool:
    """
    Attach a PDF to a Zotero item.

    Attempts to store a full copy (imported_file). Falls back to a linked_url
    attachment in any of these situations:
      - Library does not support file storage (e.g. Public Open group → 403)
      - PDF download fails (non-200, timeout)
      - Downloaded content is not a valid PDF
    """
    tmp_dir = None
    try:
        file_template = zot.item_template("attachment", "imported_file")
        file_template["title"] = filename
        file_template["filename"] = filename
        file_template["contentType"] = "application/pdf"
        file_template.pop("md5", None)
        file_template.pop("mtime", None)

        created = zot.create_items([file_template], parentid=item_key)

        if created.get("success"):
            attachment_key = created["success"]["0"]

            try:
                async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                    response = await client.get(pdf_url)
            except httpx.TimeoutException:
                logger.warning(f"Timeout downloading PDF from {pdf_url}. Falling back to linked_url.")
                _delete_attachment_item(attachment_key)
                return _attach_linked_url(item_key, pdf_url, filename)

            if response.status_code != 200:
                logger.warning(f"PDF unavailable (HTTP {response.status_code}). Falling back to linked_url.")
                _delete_attachment_item(attachment_key)
                return _attach_linked_url(item_key, pdf_url, filename)

            pdf_content = response.content
            if not pdf_content.startswith(b"%PDF"):
                logger.warning(f"Content is not a valid PDF ({len(pdf_content)} bytes). Falling back to linked_url.")
                _delete_attachment_item(attachment_key)
                return _attach_linked_url(item_key, pdf_url, filename)

            tmp_dir = tempfile.mkdtemp()
            tmp_path = os.path.join(tmp_dir, filename)
            with open(tmp_path, "wb") as f:
                f.write(pdf_content)

            upload_template = dict(file_template)
            upload_template["key"] = attachment_key
            result = zot.upload_attachments([upload_template], basedir=tmp_dir)

            if result.get("success") or result.get("unchanged"):
                logger.info(f"✓ PDF stored and attached for item {item_key}")
                return True
            else:
                logger.warning(f"File upload failed for item {item_key}: {result.get('failure', [])}")
                return False

        else:
            failed = created.get("failed", {})
            error_code = failed.get("0", {}).get("code")

            if error_code == 403:
                logger.info(f"Library does not support file storage. Falling back to linked_url attachment.")
                return _attach_linked_url(item_key, pdf_url, filename)
            else:
                logger.error(f"Zotero rejected attachment creation (code {error_code}). Details: {failed}")
                return False

    except Exception as e:
        logger.error(f"Error attaching PDF: {e}")
        logger.exception(e)
        return False
    finally:
        if tmp_dir:
            try:
                shutil.rmtree(tmp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp dir {tmp_dir}: {cleanup_error}")


# ============================================================================
# Duplicate Detection
# ============================================================================


def search_zotero_by_doi(doi: str) -> bool:
    """Check if item with DOI already exists in Zotero library."""
    try:
        normalized_doi = doi.strip().lower()

        search_terms = [doi, normalized_doi]
        if "/" in doi:
            suffix = doi.split("/", 1)[1]
            search_terms.append(suffix)

        all_results = []
        for term in search_terms:
            try:
                results = zot.items(q=term, limit=100)
                all_results.extend(results)
            except Exception:
                continue

        seen_keys: Set[str] = set()
        for item in all_results:
            item_key = item.get("key")
            if item_key in seen_keys:
                continue
            seen_keys.add(item_key)

            item_data = item.get("data", {})
            item_doi = item_data.get("DOI", "").strip().lower()
            if item_doi and item_doi == normalized_doi:
                logger.info(f"Found existing item with DOI: {doi}")
                return True

            extra = item_data.get("extra", "")
            if extra and normalized_doi in extra.lower():
                logger.info(f"Found existing item with DOI in extra field: {doi}")
                return True

        try:
            recent_items = zot.top(limit=100)
            for item in recent_items:
                item_data = item.get("data", {})
                item_doi = item_data.get("DOI", "").strip().lower()
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
        normalized_url = url.strip().rstrip("/").lower()

        url_variations = [normalized_url]
        if normalized_url.startswith("https://"):
            url_variations.append(normalized_url.replace("https://", "http://"))
        elif normalized_url.startswith("http://"):
            url_variations.append(normalized_url.replace("http://", "https://"))

        domain_match = re.search(r"https?://([^/]+)", url)
        search_terms = []
        if domain_match:
            search_terms.append(domain_match.group(1))
        search_terms.append(url)

        all_results = []
        for term in search_terms:
            try:
                results = zot.items(q=term, limit=100)
                all_results.extend(results)
            except Exception:
                continue

        seen_keys: Set[str] = set()
        for item in all_results:
            item_key = item.get("key")
            if item_key in seen_keys:
                continue
            seen_keys.add(item_key)

            item_data = item.get("data", {})
            item_url = item_data.get("url", "").strip().rstrip("/").lower()

            if item_url and item_url in url_variations:
                logger.info(f"Found existing item with URL: {url}")
                return True

            if "doi.org" in normalized_url:
                doi_match = re.search(r"doi\.org/(10\.\S+)", normalized_url)
                if doi_match:
                    doi = doi_match.group(1)
                    item_doi = item_data.get("DOI", "").strip().lower()
                    if item_doi and item_doi == doi.lower():
                        logger.info(f"Found existing item with matching DOI from URL: {url}")
                        return True

        try:
            recent_items = zot.top(limit=100)
            for item in recent_items:
                item_data = item.get("data", {})
                item_url = item_data.get("url", "").strip().rstrip("/").lower()
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

        normalized_title = " ".join(title.lower().split())

        results = zot.items(q=title, limit=20)
        for item in results:
            item_title = item.get("data", {}).get("title", "").lower()
            item_title_normalized = " ".join(item_title.split())

            if item_title_normalized == normalized_title:
                logger.info(f"Found existing item with matching title: {title[:50]}...")
                return True

        return False
    except Exception as e:
        logger.error(f"Error searching Zotero by title: {e}")
        return False


def check_duplicate_comprehensive(
    doi: Optional[str] = None,
    url: Optional[str] = None,
    title: Optional[str] = None,
) -> bool:
    """
    Comprehensive duplicate check using DOI, URL, and title (in that order).
    Returns True if a duplicate is found.
    """
    logger.debug(f"Comprehensive duplicate check - DOI: {doi}, URL: {url}, Title: {title[:50] if title else None}...")

    if doi:
        logger.debug(f"Checking DOI: {doi}")
        if search_zotero_by_doi(doi):
            logger.info(f"Duplicate found via DOI: {doi}")
            return True

    if url:
        logger.debug(f"Checking URL: {url}")
        if search_zotero_by_url(url):
            logger.info(f"Duplicate found via URL: {url}")
            return True

    if title:
        logger.debug(f"Checking title: {title[:50]}...")
        if search_zotero_by_title(title):
            logger.info(f"Duplicate found via title: {title[:50]}...")
            return True

    logger.debug("No duplicate found")
    return False


# ============================================================================
# Add to Zotero
# ============================================================================


async def add_to_zotero_by_identifier(
    identifier_type: str,
    identifier: str,
    tags: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """
    Add item to Zotero by identifier (DOI, arXiv ID, PMID) with full metadata.
    Returns (success, message).
    """
    try:
        if tags is None:
            tags = []

        metadata = None

        if identifier_type == "doi":
            logger.info(f"Checking for duplicate DOI: {identifier}")
            if check_duplicate_comprehensive(doi=identifier):
                logger.info(f"Duplicate found for DOI: {identifier}")
                return (False, "duplicate")
            logger.info(f"No duplicate found, fetching metadata for DOI: {identifier}")
            metadata = await fetch_crossref_metadata(identifier)
            if metadata:
                template = zot.item_template("journalArticle")

                template["DOI"] = identifier
                template["title"] = (
                    metadata.get("title", [""])[0]
                    if isinstance(metadata.get("title"), list)
                    else metadata.get("title", "")
                )

                if "author" in metadata:
                    creators = []
                    for author in metadata["author"]:
                        creator = {
                            "creatorType": "author",
                            "firstName": author.get("given", ""),
                            "lastName": author.get("family", ""),
                        }
                        creators.append(creator)
                    template["creators"] = creators

                container_title = metadata.get("container-title", [])
                if container_title:
                    template["publicationTitle"] = (
                        container_title[0] if isinstance(container_title, list) else container_title
                    )

                template["volume"] = metadata.get("volume", "")
                template["issue"] = metadata.get("issue", "")
                template["pages"] = metadata.get("page", "")

                published = metadata.get("published", {}) or metadata.get("published-print", {})
                if published and "date-parts" in published:
                    date_parts = published["date-parts"][0]
                    if len(date_parts) >= 1:
                        template["date"] = "-".join(map(str, date_parts))

                template["abstractNote"] = strip_html_tags(metadata.get("abstract", ""))
                template["url"] = metadata.get("URL", f"https://doi.org/{identifier}")
                template["tags"] = [{"tag": tag} for tag in tags]

                try:
                    items = zot.create_items([template])
                    logger.info(f"Added item with DOI and metadata: {identifier}")

                    if items and "successful" in items and items["successful"]:
                        item_key = items["successful"]["0"]["key"]
                        pdf_url = get_pdf_url("doi", identifier, metadata)
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

        elif identifier_type == "arxiv":
            logger.info(f"Processing arXiv paper with ID: {identifier}")
            metadata = await fetch_arxiv_metadata(identifier)
            if metadata:
                logger.info(f"Successfully fetched arXiv metadata for: {identifier}")
                if check_duplicate_comprehensive(
                    doi=metadata.get("doi"), url=metadata.get("url"), title=metadata.get("title")
                ):
                    logger.info(f"arXiv paper {identifier} is a duplicate")
                    return (False, "duplicate")

                template = zot.item_template("preprint")

                template["title"] = metadata.get("title", "")
                template["abstractNote"] = strip_html_tags(metadata.get("abstract", ""))
                template["url"] = metadata["url"]
                template["repository"] = "arXiv"
                template["archiveID"] = identifier

                if "authors" in metadata:
                    creators = []
                    for author_name in metadata["authors"]:
                        parts = author_name.rsplit(" ", 1)
                        creator = {
                            "creatorType": "author",
                            "firstName": parts[0] if len(parts) > 1 else "",
                            "lastName": parts[-1],
                        }
                        creators.append(creator)
                    template["creators"] = creators

                if "published" in metadata:
                    template["date"] = metadata["published"].split("T")[0]

                if "doi" in metadata:
                    template["DOI"] = metadata["doi"]

                template["tags"] = [{"tag": tag} for tag in tags]

                try:
                    items = zot.create_items([template])
                    logger.info(f"Added arXiv item with metadata: {identifier}")

                    if items and "successful" in items and items["successful"]:
                        item_key = items["successful"]["0"]["key"]
                        pdf_url = get_pdf_url("arxiv", identifier, metadata)
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

        elif identifier_type == "biorxiv":
            metadata = await fetch_biorxiv_metadata(identifier)
            if metadata:
                if check_duplicate_comprehensive(
                    doi=metadata.get("doi"), url=metadata.get("url"), title=metadata.get("title")
                ):
                    return (False, "duplicate")

                template = zot.item_template("preprint")

                template["title"] = metadata.get("title", "")
                template["abstractNote"] = strip_html_tags(metadata.get("abstract", ""))
                template["url"] = metadata["url"]
                template["repository"] = "bioRxiv"
                template["archiveID"] = identifier

                if "doi" in metadata:
                    template["DOI"] = metadata["doi"]

                if "authors" in metadata:
                    creators = []
                    for author_name in metadata["authors"]:
                        if "," in author_name:
                            parts = author_name.split(",", 1)
                            creator = {
                                "creatorType": "author",
                                "lastName": parts[0].strip(),
                                "firstName": parts[1].strip() if len(parts) > 1 else "",
                            }
                        else:
                            parts = author_name.rsplit(" ", 1)
                            creator = {
                                "creatorType": "author",
                                "firstName": parts[0] if len(parts) > 1 else "",
                                "lastName": parts[-1],
                            }
                        creators.append(creator)
                    template["creators"] = creators

                if "date" in metadata:
                    template["date"] = metadata["date"]

                template["tags"] = [{"tag": tag} for tag in tags]

                try:
                    items = zot.create_items([template])
                    logger.info(f"Added bioRxiv item with metadata: {identifier}")

                    if items and "successful" in items and items["successful"]:
                        item_key = items["successful"]["0"]["key"]
                        pdf_url = get_pdf_url("biorxiv", identifier, metadata)
                        if pdf_url:
                            logger.info(f"Attaching bioRxiv PDF from: {pdf_url}")
                            await download_and_attach_pdf(
                                item_key, pdf_url, f"biorxiv_{identifier.replace('/', '_')}.pdf"
                            )

                    return (True, "success")
                except Exception as e:
                    logger.error(f"Error creating Zotero item: {e}")
                    return (False, str(e))
            else:
                logger.warning(f"Could not fetch metadata for bioRxiv: {identifier}")
                return (False, "metadata_fetch_failed")

        elif identifier_type == "pubmed":
            metadata = await fetch_pubmed_metadata(identifier)
            if metadata:
                if check_duplicate_comprehensive(
                    doi=metadata.get("doi"), url=metadata.get("url"), title=metadata.get("title")
                ):
                    return (False, "duplicate")

                template = zot.item_template("journalArticle")

                template["title"] = metadata.get("title", "")
                template["publicationTitle"] = metadata.get("journal", "")
                template["volume"] = metadata.get("volume", "")
                template["issue"] = metadata.get("issue", "")
                template["pages"] = metadata.get("pages", "")
                template["date"] = metadata.get("date", "")
                template["url"] = metadata["url"]

                if "doi" in metadata:
                    template["DOI"] = metadata["doi"]

                if "authors" in metadata:
                    creators = []
                    for author_name in metadata["authors"]:
                        parts = author_name.split(" ", 1)
                        creator = {
                            "creatorType": "author",
                            "lastName": parts[0],
                            "firstName": parts[1] if len(parts) > 1 else "",
                        }
                        creators.append(creator)
                    template["creators"] = creators

                template["tags"] = [{"tag": tag} for tag in tags]

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


async def add_to_zotero_by_url(url: str, tags: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Add item to Zotero by URL, attempting to extract metadata.
    Returns (success, message).
    """
    try:
        if tags is None:
            tags = []

        metadata = await fetch_webpage_metadata(url)

        if check_duplicate_comprehensive(
            doi=metadata.get("doi") if metadata else None, url=url, title=metadata.get("title") if metadata else None
        ):
            return (False, "duplicate")

        if metadata and "doi" in metadata:
            doi = metadata["doi"]
            logger.info(f"Found DOI {doi} in webpage, using CrossRef metadata")
            return await add_to_zotero_by_identifier("doi", doi, tags=tags)

        if metadata and metadata.get("journal"):
            template = zot.item_template("journalArticle")
            template["title"] = metadata.get("title", url)
            template["publicationTitle"] = metadata.get("journal", "")
            template["date"] = metadata.get("date", "")
            template["url"] = url

            if "authors" in metadata:
                creators = []
                for author_name in metadata["authors"]:
                    parts = author_name.rsplit(" ", 1)
                    creator = {
                        "creatorType": "author",
                        "firstName": parts[0] if len(parts) > 1 else "",
                        "lastName": parts[-1],
                    }
                    creators.append(creator)
                template["creators"] = creators
        else:
            template = zot.item_template("webpage")
            template["url"] = url
            template["title"] = metadata.get("title", url) if metadata else url

            if metadata and "date" in metadata:
                template["accessDate"] = metadata["date"]

        template["extra"] = "Added via Discord Zotero Bot"
        template["tags"] = [{"tag": tag} for tag in tags]

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
    Process a single link and add to Zotero if not a duplicate.
    Returns (was_added, is_duplicate).
    """
    link_type, identifier = categorize_link(url)

    logger.info(f"Processing link: {url} (type: {link_type})")

    tags = ["discord-zotero-bot"]
    if channel_name:
        tags.append(channel_name)

    try:
        if link_type in ["doi", "arxiv", "biorxiv", "pubmed"]:
            success, message = await add_to_zotero_by_identifier(link_type, identifier, tags=tags)
        else:
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
