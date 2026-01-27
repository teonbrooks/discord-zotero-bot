#!/usr/bin/env python3
"""
Test script to verify bioRxiv link extraction and categorization.
"""

import re
from typing import Optional


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


def test_biorxiv_extraction():
    """Test bioRxiv DOI extraction."""
    
    print("="*80)
    print("BIORXIV LINK EXTRACTION TESTS")
    print("="*80)
    
    tests = [
        {
            "name": "bioRxiv content URL",
            "input": "https://www.biorxiv.org/content/10.1101/2023.05.15.540123v1",
            "expected": "10.1101/2023.05.15.540123v1"
        },
        {
            "name": "bioRxiv content URL without version",
            "input": "https://biorxiv.org/content/10.1101/2023.05.15.540123",
            "expected": "10.1101/2023.05.15.540123"
        },
        {
            "name": "bioRxiv DOI URL",
            "input": "https://doi.org/10.1101/2023.05.15.540123",
            "expected": "10.1101/2023.05.15.540123"
        },
        {
            "name": "Bare bioRxiv DOI",
            "input": "Check out this paper: 10.1101/2023.05.15.540123",
            "expected": "10.1101/2023.05.15.540123"
        },
        {
            "name": "bioRxiv DOI with version",
            "input": "10.1101/2023.05.15.540123v2",
            "expected": "10.1101/2023.05.15.540123v2"
        },
        {
            "name": "Non-bioRxiv DOI (should not match)",
            "input": "https://doi.org/10.1038/s41591-025-04133-4",
            "expected": None
        },
        {
            "name": "arXiv URL (should not match)",
            "input": "https://arxiv.org/abs/2401.12345",
            "expected": None
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n{'='*80}")
        print(f"Test: {test['name']}")
        print(f"{'='*80}")
        
        result = extract_biorxiv_doi(test['input'])
        
        print(f"\nInput:")
        print(f"  {test['input']}")
        
        print(f"\nExpected:")
        print(f"  {test['expected']}")
        
        print(f"\nGot:")
        print(f"  {result}")
        
        if result == test['expected']:
            print("\n✓ PASSED")
            passed += 1
        else:
            print("\n✗ FAILED")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'='*80}\n")
    
    return failed == 0


if __name__ == "__main__":
    success = test_biorxiv_extraction()
    exit(0 if success else 1)
