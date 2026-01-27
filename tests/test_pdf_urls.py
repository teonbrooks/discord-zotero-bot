#!/usr/bin/env python3
"""
Test PDF URL generation for different paper sources.

This script tests the get_pdf_url() function to ensure it generates
correct PDF URLs for various identifier types.
"""

import sys
sys.path.insert(0, '..')

from typing import Dict, Optional

def get_pdf_url(identifier_type: str, identifier: str, metadata: Optional[Dict] = None) -> Optional[str]:
    """
    Get PDF URL for a given identifier type and identifier.
    (Copied from zotero-bot.py for testing)
    """
    try:
        if identifier_type == 'arxiv':
            return f"https://arxiv.org/pdf/{identifier}.pdf"
        
        elif identifier_type == 'biorxiv':
            if identifier.startswith('10.1101/'):
                numeric_id = identifier.replace('10.1101/', '')
                version = 'v1'
                if metadata and 'url' in metadata:
                    import re
                    version_match = re.search(r'(v\d+)', metadata['url'])
                    if version_match:
                        version = version_match.group(1)
                return f"https://www.biorxiv.org/content/10.1101/{numeric_id}{version}.full.pdf"
            return None
        
        elif identifier_type == 'doi':
            if metadata:
                links = metadata.get('link', [])
                for link in links:
                    if link.get('content-type') == 'application/pdf':
                        return link.get('URL')
            return None
        
        elif identifier_type == 'pubmed':
            return None
        
        else:
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_arxiv_urls():
    """Test arXiv PDF URL generation."""
    print("Testing arXiv PDF URLs...")
    
    tests = [
        ('2404.05553', 'https://arxiv.org/pdf/2404.05553.pdf'),
        ('1234.5678', 'https://arxiv.org/pdf/1234.5678.pdf'),
        ('0704.0001', 'https://arxiv.org/pdf/0704.0001.pdf'),
        ('2301.12345v2', 'https://arxiv.org/pdf/2301.12345v2.pdf'),
    ]
    
    passed = 0
    failed = 0
    
    for arxiv_id, expected_url in tests:
        result = get_pdf_url('arxiv', arxiv_id)
        if result == expected_url:
            print(f"  ✓ {arxiv_id} -> {result}")
            passed += 1
        else:
            print(f"  ✗ {arxiv_id}")
            print(f"    Expected: {expected_url}")
            print(f"    Got:      {result}")
            failed += 1
    
    print(f"\narXiv Tests: {passed} passed, {failed} failed\n")
    return failed == 0


def test_biorxiv_urls():
    """Test bioRxiv PDF URL generation."""
    print("Testing bioRxiv PDF URLs...")
    
    tests = [
        (
            '10.1101/2023.05.15.540123',
            None,
            'https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1.full.pdf'
        ),
        (
            '10.1101/2023.05.15.540123',
            {'url': 'https://www.biorxiv.org/content/10.1101/2023.05.15.540123v2'},
            'https://www.biorxiv.org/content/10.1101/2023.05.15.540123v2.full.pdf'
        ),
        (
            '10.1101/2024.01.01.123456',
            {'url': 'https://www.biorxiv.org/content/10.1101/2024.01.01.123456v1'},
            'https://www.biorxiv.org/content/10.1101/2024.01.01.123456v1.full.pdf'
        ),
    ]
    
    passed = 0
    failed = 0
    
    for doi, metadata, expected_url in tests:
        result = get_pdf_url('biorxiv', doi, metadata)
        if result == expected_url:
            print(f"  ✓ {doi} -> {result}")
            passed += 1
        else:
            print(f"  ✗ {doi}")
            print(f"    Expected: {expected_url}")
            print(f"    Got:      {result}")
            failed += 1
    
    print(f"\nbioRxiv Tests: {passed} passed, {failed} failed\n")
    return failed == 0


def test_doi_urls():
    """Test DOI PDF URL extraction from metadata."""
    print("Testing DOI PDF URL extraction...")
    
    # Test with PDF link in metadata
    metadata_with_pdf = {
        'link': [
            {'content-type': 'text/html', 'URL': 'https://example.com/paper.html'},
            {'content-type': 'application/pdf', 'URL': 'https://example.com/paper.pdf'},
        ]
    }
    
    result = get_pdf_url('doi', '10.1234/example', metadata_with_pdf)
    if result == 'https://example.com/paper.pdf':
        print(f"  ✓ DOI with PDF link -> {result}")
    else:
        print(f"  ✗ DOI with PDF link")
        print(f"    Expected: https://example.com/paper.pdf")
        print(f"    Got:      {result}")
        return False
    
    # Test without PDF link
    metadata_no_pdf = {
        'link': [
            {'content-type': 'text/html', 'URL': 'https://example.com/paper.html'},
        ]
    }
    
    result = get_pdf_url('doi', '10.1234/example', metadata_no_pdf)
    if result is None:
        print(f"  ✓ DOI without PDF link -> None (correct)")
    else:
        print(f"  ✗ DOI without PDF link")
        print(f"    Expected: None")
        print(f"    Got:      {result}")
        return False
    
    print(f"\nDOI Tests: 2 passed, 0 failed\n")
    return True


def test_pubmed_urls():
    """Test PubMed PDF URL (should return None for now)."""
    print("Testing PubMed PDF URLs...")
    
    result = get_pdf_url('pubmed', '12345678')
    if result is None:
        print(f"  ✓ PubMed -> None (not yet implemented)")
        print(f"\nPubMed Tests: 1 passed, 0 failed\n")
        return True
    else:
        print(f"  ✗ PubMed should return None")
        print(f"    Got: {result}")
        print(f"\nPubMed Tests: 0 passed, 1 failed\n")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("PDF URL Generation Tests")
    print("=" * 60)
    print()
    
    results = []
    results.append(("arXiv", test_arxiv_urls()))
    results.append(("bioRxiv", test_biorxiv_urls()))
    results.append(("DOI", test_doi_urls()))
    results.append(("PubMed", test_pubmed_urls()))
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    total_passed = sum(1 for _, passed in results if passed)
    total_failed = len(results) - total_passed
    
    for category, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {category:15} {status}")
    
    print()
    print(f"Total: {total_passed}/{len(results)} test categories passed")
    
    if total_failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total_failed} test category(ies) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
