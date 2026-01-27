# Test Suite

This directory contains test scripts for the Zotero Discord Bot.

## Test Files

### 📄 `test_pdf_urls.py`
Tests PDF URL generation for different paper sources.

**What it tests**:
- arXiv PDF URL generation
- bioRxiv PDF URL generation with version handling
- DOI PDF link extraction from metadata
- PubMed PDF handling (not yet implemented)

**Run**:
```bash
python test_pdf_urls.py
```

**Expected output**: All 4 test categories pass (10 total tests)

---

### 🧬 `test_arxiv_live.py`
Tests arXiv paper detection and metadata fetching.

**What it tests**:
- arXiv ID extraction from various URL formats
- arXiv DOI format (`10.48550/arXiv.*`)
- API connectivity and response parsing
- Metadata completeness

**Run**:
```bash
uv run python test_arxiv_live.py
```

**Expected output**: All tests pass with metadata displayed

---

### 🧬 `test_biorxiv.py`
Tests bioRxiv DOI detection patterns.

**What it tests**:
- bioRxiv DOI extraction (`10.1101/*`)
- Various URL formats
- Version handling (v1, v2, etc.)
- Non-bioRxiv DOI exclusion

**Run**:
```bash
uv run python test_biorxiv.py
```

**Expected output**: 7/7 tests pass

---

### 📝 `test_abstract_cleaning.py`
Tests HTML/XML tag removal from abstracts.

**What it tests**:
- JATS XML format cleaning
- Title tag removal
- HTML paragraph tags
- Nested tags
- Whitespace normalization

**Run**:
```bash
uv run python test_abstract_cleaning.py
```

**Expected output**: 10/10 tests pass

---

### 🔍 `test_duplicates.py`
Interactive tool to test duplicate detection in your Zotero library.

**What it tests**:
- Library contents listing
- DOI search functionality
- URL search functionality
- Duplicate detection logic

**Run**:
```bash
uv run python test_duplicates.py
```

**Features**:
- Shows recent library items
- Manual DOI/URL search testing
- Interactive menu system

---

## Running All Tests

### Quick Check
```bash
cd tests
for test in test_*.py; do
    echo "Running $test..."
    uv run python "$test" || echo "FAILED: $test"
done
```

### Individual Tests
```bash
# Test arXiv (requires network)
uv run python test_arxiv_live.py

# Test bioRxiv (offline)
uv run python test_biorxiv.py

# Test abstract cleaning (offline)
uv run python test_abstract_cleaning.py

# Test duplicates (requires Zotero config)
uv run python test_duplicates.py
```

## Test Requirements

### Network Tests
- `test_arxiv_live.py` - Requires internet connection
- `test_duplicates.py` - Requires Zotero API access

### Offline Tests
- `test_biorxiv.py` - Pure regex testing
- `test_abstract_cleaning.py` - Pure string manipulation

### Configuration
Some tests require `.env` file with:
```bash
ZOTERO_TOKEN=your_token_here
ZOTERO_GROUP_ID=your_group_id_here
```

## Expected Results

### ✅ All Tests Passing
```
test_arxiv_live.py: 4/4 passed
test_biorxiv.py: 7/7 passed
test_abstract_cleaning.py: 10/10 passed
test_duplicates.py: Interactive (manual verification)
```

### ⚠️ Common Issues

**Network timeout**:
- Check internet connection
- arXiv API may be slow
- Increase timeout if needed

**Import errors**:
- Run with `uv run python`
- Ensures correct environment

**Zotero auth errors**:
- Check `.env` file
- Verify API token
- Confirm group ID

## Adding New Tests

### Template
```python
#!/usr/bin/env python3
"""
Test description here.
"""

def test_feature():
    """Test a specific feature."""
    # Setup
    input_data = "test"
    expected = "result"
    
    # Execute
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ PASSED")

if __name__ == "__main__":
    test_feature()
```

### Best Practices
1. Clear test names
2. Document what's being tested
3. Show expected vs actual
4. Use emoji for visual feedback (✓ ✗)
5. Return non-zero exit code on failure

## Continuous Testing

### Before Committing
```bash
# Run all offline tests
python test_biorxiv.py && python test_abstract_cleaning.py

# Run network tests if available
python test_arxiv_live.py
```

### After Changes
Test affected functionality:
- Changed arXiv code? Run `test_arxiv_live.py`
- Changed bioRxiv code? Run `test_biorxiv.py`
- Changed abstract cleaning? Run `test_abstract_cleaning.py`
- Changed duplicate detection? Run `test_duplicates.py`

## Debugging Failed Tests

### Enable Verbose Output
Most tests have detailed output. Check:
- Input values
- Expected results
- Actual results
- Error messages

### Common Fixes
1. **Import errors** → Use `uv run python`
2. **Network timeouts** → Check connection
3. **API errors** → Verify credentials
4. **Pattern mismatches** → Check regex patterns

## Future Tests

### Planned
- [ ] PubMed detection tests
- [ ] DOI detection tests
- [ ] End-to-end bot tests
- [ ] Discord message handling tests
- [ ] Zotero item creation tests
- [ ] Performance tests
- [ ] Rate limiting tests

### Contributing
To add a test:
1. Create `test_[feature].py`
2. Follow template above
3. Add to this README
4. Ensure it passes
5. Document requirements

---

**Need help?** See [Testing Guide](../docs/testing.md) in the docs folder.
