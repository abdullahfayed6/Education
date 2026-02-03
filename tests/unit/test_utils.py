"""
Unit tests for core utilities.
"""

import pytest

from src.core.utils import (
    generate_id,
    sanitize_string,
    validate_email,
    truncate_text,
    chunk_list,
    merge_dicts
)


class TestUtils:
    """Test utility functions."""
    
    def test_generate_id(self):
        """Test ID generation."""
        id1 = generate_id()
        id2 = generate_id()
        
        assert len(id1) > 0
        assert id1 != id2  # Should be unique
    
    def test_generate_id_with_prefix(self):
        """Test ID generation with prefix."""
        user_id = generate_id(prefix="user_")
        
        assert user_id.startswith("user_")
        assert len(user_id) > 5
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        dangerous = "<script>alert('xss')</script>"
        safe = sanitize_string(dangerous)
        
        assert "<" not in safe
        assert ">" not in safe
    
    def test_sanitize_string_max_length(self):
        """Test string truncation."""
        long_text = "a" * 2000
        sanitized = sanitize_string(long_text, max_length=100)
        
        assert len(sanitized) == 100
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user@company.co.uk") is True
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
    
    def test_truncate_text(self):
        """Test text truncation."""
        long_text = "This is a very long text that needs to be truncated"
        short = truncate_text(long_text, max_length=20)
        
        assert len(short) <= 20
        assert short.endswith("...")
    
    def test_truncate_text_no_truncation(self):
        """Test text that doesn't need truncation."""
        short_text = "Short"
        result = truncate_text(short_text, max_length=100)
        
        assert result == short_text
    
    def test_chunk_list(self):
        """Test list chunking."""
        items = list(range(10))
        chunks = chunk_list(items, chunk_size=3)
        
        assert len(chunks) == 4  # [0,1,2], [3,4,5], [6,7,8], [9]
        assert chunks[0] == [0, 1, 2]
        assert chunks[-1] == [9]
    
    def test_merge_dicts(self):
        """Test dictionary merging."""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        
        merged = merge_dicts(dict1, dict2)
        
        assert merged["a"] == 1
        assert merged["b"]["c"] == 2
        assert merged["b"]["d"] == 3
        assert merged["e"] == 4
