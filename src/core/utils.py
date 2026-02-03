"""Core utility functions and helpers."""

from __future__ import annotations

import hashlib
import secrets
import re
from typing import Any
from datetime import datetime, timedelta


def generate_id(prefix: str = "", length: int = 16) -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of random part
        
    Returns:
        Unique ID string
    """
    random_part = secrets.token_urlsafe(length)[:length]
    return f"{prefix}{random_part}" if prefix else random_part


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password
        
    Returns:
        True if password matches
    """
    return hash_password(password) == hashed


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input string.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    # Remove potentially harmful characters
    text = text.strip()
    text = re.sub(r'[<>]', '', text)  # Remove angle brackets
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def calculate_ttl(days: int = 30) -> int:
    """
    Calculate TTL timestamp for Cosmos DB.
    
    Args:
        days: Number of days until expiration
        
    Returns:
        Unix timestamp for TTL
    """
    expiration = datetime.utcnow() + timedelta(days=days)
    return int(expiration.timestamp())


def format_error(error: Exception) -> dict[str, Any]:
    """
    Format exception for logging/response.
    
    Args:
        error: Exception object
        
    Returns:
        Formatted error dictionary
    """
    return {
        "type": type(error).__name__,
        "message": str(error),
        "args": error.args
    }


def chunk_list(items: list, chunk_size: int) -> list[list]:
    """
    Split list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address
        
    Returns:
        True if valid format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
