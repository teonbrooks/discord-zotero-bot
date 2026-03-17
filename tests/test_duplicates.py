#!/usr/bin/env python3
"""
Test script to check duplicate detection in Zotero library.
Run this to diagnose duplicate detection issues.
"""

import os
import sys
from dotenv import load_dotenv
from pyzotero import zotero

# Load environment variables
load_dotenv()
ZOTERO_TOKEN = os.getenv("ZOTERO_TOKEN")
ZOTERO_GROUP_ID = os.getenv("ZOTERO_GROUP_ID")

if not ZOTERO_TOKEN or not ZOTERO_GROUP_ID:
    print("ERROR: ZOTERO_TOKEN and ZOTERO_GROUP_ID must be set in .env file")
    sys.exit(1)

# Initialize Zotero client
zot = zotero.Zotero(ZOTERO_GROUP_ID, "group", ZOTERO_TOKEN)


def test_library_contents():
    """Display recent items in the library."""
    print("\n" + "=" * 80)
    print("RECENT ITEMS IN LIBRARY (last 20)")
    print("=" * 80)

    try:
        items = zot.top(limit=20)
        print(f"\nFound {len(items)} items:")

        for i, item in enumerate(items, 1):
            data = item.get("data", {})
            title = data.get("title", "No title")
            doi = data.get("DOI", "No DOI")
            url = data.get("url", "No URL")
            item_type = data.get("itemType", "unknown")

            print(f"\n{i}. {title[:60]}...")
            print(f"   Type: {item_type}")
            print(f"   DOI: {doi}")
            print(f"   URL: {url}")

    except Exception as e:
        print(f"Error fetching items: {e}")


def test_doi_search(doi_to_check):
    """Test if a DOI exists in the library."""
    print("\n" + "=" * 80)
    print(f"TESTING DOI SEARCH: {doi_to_check}")
    print("=" * 80)

    normalized_doi = doi_to_check.strip().lower()
    print(f"Normalized DOI: {normalized_doi}")

    # Try text search
    print("\n1. Text search results:")
    try:
        results = zot.items(q=doi_to_check, limit=100)
        print(f"   Found {len(results)} results with text search")

        found = False
        for item in results:
            data = item.get("data", {})
            item_doi = data.get("DOI", "").strip().lower()
            if item_doi == normalized_doi:
                print(f"   ✓ MATCH FOUND: {data.get('title', 'No title')[:60]}...")
                found = True
                break

        if not found and results:
            print("   ✗ No exact DOI match in text search results")
            print("   Checking what DOIs were returned:")
            for item in results[:5]:
                data = item.get("data", {})
                print(f"     - {data.get('DOI', 'No DOI')}")

    except Exception as e:
        print(f"   Error in text search: {e}")

    # Try checking recent items
    print("\n2. Checking recent items:")
    try:
        recent = zot.top(limit=100)
        print(f"   Checking {len(recent)} recent items")

        found = False
        for item in recent:
            data = item.get("data", {})
            item_doi = data.get("DOI", "").strip().lower()
            if item_doi == normalized_doi:
                print(f"   ✓ MATCH FOUND in recent items: {data.get('title', 'No title')[:60]}...")
                found = True
                break

        if not found:
            print("   ✗ No match in recent items")

    except Exception as e:
        print(f"   Error checking recent items: {e}")


def test_url_search(url_to_check):
    """Test if a URL exists in the library."""
    print("\n" + "=" * 80)
    print(f"TESTING URL SEARCH: {url_to_check}")
    print("=" * 80)

    normalized_url = url_to_check.strip().rstrip("/").lower()
    print(f"Normalized URL: {normalized_url}")

    # Try text search
    print("\n1. Text search results:")
    try:
        results = zot.items(q=url_to_check, limit=100)
        print(f"   Found {len(results)} results with text search")

        found = False
        for item in results:
            data = item.get("data", {})
            item_url = data.get("url", "").strip().rstrip("/").lower()
            if item_url == normalized_url:
                print(f"   ✓ MATCH FOUND: {data.get('title', 'No title')[:60]}...")
                found = True
                break

        if not found and results:
            print("   ✗ No exact URL match in text search results")

    except Exception as e:
        print(f"   Error in text search: {e}")

    # Try checking recent items
    print("\n2. Checking recent items:")
    try:
        recent = zot.top(limit=100)
        print(f"   Checking {len(recent)} recent items")

        found = False
        for item in recent:
            data = item.get("data", {})
            item_url = data.get("url", "").strip().rstrip("/").lower()
            if item_url == normalized_url:
                print(f"   ✓ MATCH FOUND in recent items: {data.get('title', 'No title')[:60]}...")
                found = True
                break

        if not found:
            print("   ✗ No match in recent items")

    except Exception as e:
        print(f"   Error checking recent items: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ZOTERO DUPLICATE DETECTION TEST")
    print("=" * 80)
    print(f"Group ID: {ZOTERO_GROUP_ID}")

    # Show library contents
    test_library_contents()

    # Test with user input
    print("\n" + "=" * 80)
    print("MANUAL TESTING")
    print("=" * 80)

    while True:
        print("\nOptions:")
        print("1. Test DOI search")
        print("2. Test URL search")
        print("3. Show library contents again")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            doi = input("Enter DOI to check (e.g., 10.1038/s41591-025-04133-4): ").strip()
            if doi:
                test_doi_search(doi)
        elif choice == "2":
            url = input("Enter URL to check: ").strip()
            if url:
                test_url_search(url)
        elif choice == "3":
            test_library_contents()
        elif choice == "4":
            print("\nExiting...")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
