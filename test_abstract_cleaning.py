#!/usr/bin/env python3
"""
Test script to verify abstract cleaning works correctly.
"""

import re


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


def test_abstract_cleaning():
    """Test various abstract formats."""
    
    print("="*80)
    print("ABSTRACT CLEANING TESTS")
    print("="*80)
    
    tests = [
        {
            "name": "JATS XML Format (Nature journals)",
            "input": '<jats:title>Abstract</jats:title><jats:p>Sleep is a fundamental biological process with broad implications for physical and mental health, yet its complex relationship with disease remains poorly understood.</jats:p>',
            "expected": "Sleep is a fundamental biological process with broad implications for physical and mental health, yet its complex relationship with disease remains poorly understood."
        },
        {
            "name": "Simple HTML paragraphs",
            "input": '<p>This is the first paragraph.</p><p>This is the second paragraph.</p>',
            "expected": "This is the first paragraph. This is the second paragraph."
        },
        {
            "name": "Nested tags",
            "input": '<div><p><strong>Bold text</strong> and <em>italic text</em> in abstract.</p></div>',
            "expected": "Bold text and italic text in abstract."
        },
        {
            "name": "Self-closing tags",
            "input": 'Text before<br/>Text after',
            "expected": "Text before Text after"
        },
        {
            "name": "Multiple spaces and newlines",
            "input": '<p>Text   with    multiple     spaces\n\nand newlines</p>',
            "expected": "Text with multiple spaces and newlines"
        },
        {
            "name": "Plain text (no tags)",
            "input": "This is plain text without any tags.",
            "expected": "This is plain text without any tags."
        },
        {
            "name": "Empty string",
            "input": "",
            "expected": ""
        },
        {
            "name": "Title tag removal (lowercase)",
            "input": '<title>Summary</title><p>This is the actual content.</p>',
            "expected": "This is the actual content."
        },
        {
            "name": "Title tag removal (uppercase)",
            "input": '<TITLE>ABSTRACT</TITLE><p>Content here.</p>',
            "expected": "Content here."
        },
        {
            "name": "Multiple title variants",
            "input": '<jats:title>Abstract</jats:title><jats:sec><jats:title>Background</jats:title><jats:p>Background info.</jats:p></jats:sec>',
            "expected": "Background info."
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n{'='*80}")
        print(f"Test: {test['name']}")
        print(f"{'='*80}")
        
        result = strip_html_tags(test['input'])
        
        print(f"\nInput:")
        print(f"  {test['input'][:100]}{'...' if len(test['input']) > 100 else ''}")
        
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
    success = test_abstract_cleaning()
    exit(0 if success else 1)
