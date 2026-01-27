#!/usr/bin/env python3
"""
Live test of arXiv metadata fetching to diagnose issues.
"""

import asyncio
import httpx
import xml.etree.ElementTree as ET
import re
from typing import Optional


def extract_arxiv_id(text: str) -> Optional[str]:
    """Extract arXiv ID from text or URL."""
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


async def fetch_arxiv_metadata(arxiv_id: str):
    """Fetch metadata from arXiv API."""
    print(f"\n{'='*80}")
    print(f"Testing arXiv metadata fetch for ID: {arxiv_id}")
    print(f"{'='*80}\n")
    
    try:
        # Remove version suffix if present
        base_id = arxiv_id.split('v')[0]
        
        # Try HTTPS first
        url_https = f"https://export.arxiv.org/api/query?id_list={base_id}"
        url_http = f"http://export.arxiv.org/api/query?id_list={base_id}"
        
        print(f"Base ID: {base_id}")
        print(f"URL (HTTPS): {url_https}")
        print(f"URL (HTTP): {url_http}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try HTTPS
            print(f"\n1. Trying HTTPS...")
            try:
                response = await client.get(url_https)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   Response length: {len(response.content)} bytes")
                    print(f"   Content type: {response.headers.get('content-type', 'unknown')}")
                    
                    # Parse XML
                    print(f"\n2. Parsing XML...")
                    root = ET.fromstring(response.content)
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    
                    # Find entry
                    entry = root.find('atom:entry', ns)
                    
                    if entry is not None:
                        print(f"   ✓ Found entry element")
                        
                        # Extract fields
                        metadata = {}
                        
                        # Title
                        title_elem = entry.find('atom:title', ns)
                        if title_elem is not None:
                            metadata['title'] = title_elem.text.strip()
                            print(f"   ✓ Title: {metadata['title'][:80]}...")
                        
                        # Authors
                        authors = []
                        for author in entry.findall('atom:author', ns):
                            name_elem = author.find('atom:name', ns)
                            if name_elem is not None:
                                authors.append(name_elem.text.strip())
                        metadata['authors'] = authors
                        print(f"   ✓ Authors: {len(authors)} found")
                        if authors:
                            print(f"      First author: {authors[0]}")
                        
                        # Abstract
                        summary_elem = entry.find('atom:summary', ns)
                        if summary_elem is not None:
                            metadata['abstract'] = summary_elem.text.strip()
                            print(f"   ✓ Abstract: {len(metadata['abstract'])} chars")
                        
                        # Published
                        published_elem = entry.find('atom:published', ns)
                        if published_elem is not None:
                            metadata['published'] = published_elem.text.strip()
                            print(f"   ✓ Published: {metadata['published']}")
                        
                        # URL
                        metadata['url'] = f"https://arxiv.org/abs/{arxiv_id}"
                        print(f"   ✓ URL: {metadata['url']}")
                        
                        print(f"\n✅ SUCCESS - Metadata fetched successfully")
                        return metadata
                    else:
                        print(f"   ✗ No entry element found")
                        print(f"\n   Root tag: {root.tag}")
                        print(f"   Root children:")
                        for child in root:
                            print(f"      - {child.tag}")
                        
                        # Check for errors
                        error = root.find('.//{http://www.w3.org/2005/Atom}title')
                        if error is not None and 'error' in error.text.lower():
                            print(f"   API Error: {error.text}")
                        
                        return None
                else:
                    print(f"   ✗ HTTP error: {response.status_code}")
                    
            except Exception as e:
                print(f"   ✗ HTTPS failed: {e}")
                
                # Try HTTP
                print(f"\n3. Trying HTTP...")
                try:
                    response = await client.get(url_http)
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"   Response length: {len(response.content)} bytes")
                        # Same parsing as above...
                        print(f"   (HTTP worked, but HTTPS should be used)")
                    
                except Exception as e2:
                    print(f"   ✗ HTTP also failed: {e2}")
        
        return None
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Test arXiv extraction and metadata fetching."""
    
    test_cases = [
        "https://doi.org/10.48550/arXiv.2404.05553",  # arXiv DOI format
        "https://arxiv.org/abs/2404.05553",  # Standard arXiv URL
        "https://arxiv.org/abs/1706.03762",  # "Attention is All You Need" - real paper
        "2404.05553",  # Bare ID
    ]
    
    print("\n" + "="*80)
    print("ARXIV LIVE TEST")
    print("="*80)
    
    for test_url in test_cases:
        print(f"\n{'='*80}")
        print(f"Test: {test_url}")
        print(f"{'='*80}")
        
        # Extract ID
        arxiv_id = extract_arxiv_id(test_url)
        print(f"Extracted ID: {arxiv_id}")
        
        if arxiv_id:
            # Fetch metadata
            metadata = await fetch_arxiv_metadata(arxiv_id)
            
            if metadata:
                print(f"\n✅ Test PASSED")
            else:
                print(f"\n❌ Test FAILED - No metadata returned")
        else:
            print(f"\n❌ Test FAILED - Could not extract arXiv ID")
        
        print("\n" + "-"*80)
    
    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
