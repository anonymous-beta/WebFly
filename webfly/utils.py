"""
WebFly Utilities
Helper functions and utilities
"""

import hashlib
import random
import string
import os
from typing import Dict, List
from urllib.parse import urlparse

def generate_id(url: str) -> str:
    """Generate short ID from URL"""
    return hashlib.md5(url.encode()).hexdigest()[:8]

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def load_wordlist(path: str) -> List[str]:
    """Load wordlist from file"""
    words = []
    try:
        with open(path, 'r') as f:
            for line in f:
                word = line.strip()
                if word and not word.startswith('#'):
                    words.append(word)
    except FileNotFoundError:
        pass
    return words

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lower()

def format_bytes(size: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"
