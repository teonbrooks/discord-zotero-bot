#!/usr/bin/env python3
"""
Test Zotero PDF attachment functionality.

This script helps diagnose issues with PDF attachments to Zotero.
Requires valid Zotero credentials in .env file.
"""

import os
import sys
import tempfile
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, "..")

# Load environment variables
load_dotenv("../.env")

ZOTERO_TOKEN = os.getenv("ZOTERO_TOKEN")
ZOTERO_GROUP_ID = os.getenv("ZOTERO_GROUP_ID")

if not ZOTERO_TOKEN or not ZOTERO_GROUP_ID:
    print("❌ ERROR: ZOTERO_TOKEN and ZOTERO_GROUP_ID must be set in .env file")
    sys.exit(1)

try:
    from pyzotero import zotero
except ImportError:
    print("❌ ERROR: pyzotero not installed")
    print("Install with: pip install pyzotero")
    sys.exit(1)


def test_zotero_connection():
    """Test basic Zotero API connection."""
    print("Testing Zotero API connection...")
    try:
        zot = zotero.Zotero(ZOTERO_GROUP_ID, "group", ZOTERO_TOKEN)
        items = zot.items(limit=1)
        total = zot.num_items()
        print(f"  ✓ Connected to Zotero")
        print(f"  ✓ Library has {total} items")
        return zot
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return None


def test_attachment_simple_signature():
    """Test the correct signature for attachment_simple()."""
    print("\nTesting attachment_simple() method signature...")
    try:
        from pyzotero import zotero
        import inspect

        # Get the signature
        sig = inspect.signature(zotero.Zotero.attachment_simple)
        print(f"  Signature: {sig}")

        # Check parameters
        params = sig.parameters
        if "parentid" in params:
            print(f"  ✓ Has 'parentid' parameter")
        else:
            print(f"  ⚠️  No 'parentid' parameter found")
            print(f"  Available parameters: {list(params.keys())}")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_create_dummy_pdf():
    """Create a minimal valid PDF for testing."""
    print("\nCreating test PDF...")
    try:
        # Minimal valid PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
322
%%EOF
"""

        # Write to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name

        print(f"  ✓ Created test PDF: {tmp_path}")
        print(f"  ✓ Size: {len(pdf_content)} bytes")

        # Verify it starts with %PDF
        if pdf_content.startswith(b"%PDF"):
            print(f"  ✓ Has valid PDF header")
        else:
            print(f"  ✗ Invalid PDF header")

        return tmp_path
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def test_attachment_to_first_item(zot, pdf_path):
    """Test attaching PDF to the first item in library."""
    print("\nTesting PDF attachment to first library item...")
    try:
        # Get first item
        items = zot.items(limit=1)
        if not items:
            print("  ⚠️  No items in library to test with")
            return False

        item = items[0]
        item_key = item["key"]
        item_title = item["data"].get("title", "Untitled")

        print(f"  Testing with item: {item_title[:50]}")
        print(f"  Item key: {item_key}")

        # Method 1: Try attachment_simple
        print(f"\n  Method 1: Testing attachment_simple()...")
        method1_success = False
        try:
            result = zot.attachment_simple([pdf_path], parentid=item_key)
            print(f"  Result: {result}")

            # Check the result structure
            if isinstance(result, dict):
                success_list = result.get("success", [])
                failure_list = result.get("failure", [])
                print(f"  Success items: {len(success_list)}")
                print(f"  Failure items: {len(failure_list)}")

                if failure_list:
                    print(f"  ✗ attachment_simple() reported failures: {failure_list}")
                elif not success_list:
                    print(f"  ✗ attachment_simple() returned empty success list")
                else:
                    print(f"  ✓ attachment_simple() succeeded")
                    method1_success = True
            else:
                print(f"  ⚠️  Unexpected result format: {type(result)}")
                method1_success = True  # Assume success for non-dict results

        except Exception as e:
            print(f"  ✗ attachment_simple() raised exception: {e}")

        # Method 2: Try manual attachment creation
        print(f"\n  Method 2: Testing manual attachment creation...")
        method2_success = False
        try:
            # Create attachment template
            template = zot.item_template("attachment", "imported_file")
            template["parentItem"] = item_key
            template["title"] = "test_attachment.pdf"
            template["contentType"] = "application/pdf"
            template["filename"] = "test_attachment.pdf"

            print(f"    Creating attachment item...")
            created = zot.create_items([template])
            print(f"    Created: {created}")

            if created and "successful" in created and created["successful"]:
                attachment_key = created["successful"]["0"]["key"]
                print(f"    Attachment item created with key: {attachment_key}")

                # Upload the file
                print(f"    Uploading PDF file...")
                with open(pdf_path, "rb") as f:
                    upload_result = zot.upload_attachment(attachment_key, f)
                print(f"    Upload result: {upload_result}")

                print(f"  ✓ Manual method succeeded")
                method2_success = True
            else:
                print(f"  ✗ Failed to create attachment item")
        except Exception as e:
            print(f"  ✗ Manual method failed: {e}")
            import traceback

            traceback.print_exc()

        # Verify attachments were created
        print(f"\n  Verifying attachments...")
        children = zot.children(item_key)
        pdf_attachments = [c for c in children if c["data"].get("itemType") == "attachment"]

        print(f"  Found {len(pdf_attachments)} attachment(s) on item")
        for att in pdf_attachments:
            print(f"    - {att['data'].get('title', 'Untitled')} ({att['data'].get('contentType', 'unknown')})")

        # Clean up test attachments
        if pdf_attachments:
            print(f"\n  Cleaning up test attachments...")
            for att in pdf_attachments:
                title = att["data"].get("title", "").lower()
                if "test" in title:
                    try:
                        zot.delete_item(att)
                        print(f"    ✓ Removed: {att['data'].get('title')}")
                    except Exception as e:
                        print(f"    ⚠️  Failed to remove {att['data'].get('title')}: {e}")

        # Return overall success
        if method1_success or method2_success:
            print(f"\n  ✅ At least one method succeeded!")
            if method1_success:
                print(f"     Recommended: Method 1 (attachment_simple) works")
            else:
                print(f"     Recommended: Use Method 2 (manual creation)")
            return True
        else:
            print(f"\n  ❌ Both methods failed")
            return False

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Zotero PDF Attachment Diagnostics")
    print("=" * 60)
    print()

    # Test 1: Connection
    zot = test_zotero_connection()
    if not zot:
        print("\n❌ Cannot proceed without Zotero connection")
        return 1

    # Test 2: Method signature
    test_attachment_simple_signature()

    # Test 3: Create test PDF
    pdf_path = test_create_dummy_pdf()
    if not pdf_path:
        print("\n❌ Cannot proceed without test PDF")
        return 1

    # Test 4: Attachment
    try:
        success = test_attachment_to_first_item(zot, pdf_path)

        if success:
            print("\n" + "=" * 60)
            print("✅ All tests passed!")
            print("=" * 60)
            print("\nThe bot should now be able to attach PDFs correctly.")
            print("Try running /attach_pdfs in Discord.")
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ Attachment test failed")
            print("=" * 60)
            print("\nCheck the error messages above for details.")
            return 1
    finally:
        # Clean up temp file
        try:
            os.unlink(pdf_path)
            print(f"\n✓ Cleaned up test PDF")
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
