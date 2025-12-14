import os

def ensure_directory_exists(directory):
    """
    Creates the specified directory if it does not exist.
    
    :param directory: Path to the directory.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

import re

def sanitize_filename(filename):
    """
    Sanitizes a filename by removing or replacing invalid characters and control characters.
    
    :param filename: Original filename.
    :return: Sanitized filename.
    """
    # Replace invalid filename characters and control characters with underscore
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

def validate_url(url):
    """
    Validates if the provided string is a valid URL.
    
    :param url: URL string to validate.
    :return: True if valid, False otherwise.
    """
    return url.startswith("http://") or url.startswith("https://")

__all__ = [
    "ensure_directory_exists",
    "sanitize_filename",
    "validate_url",
]
