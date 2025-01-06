import os

def ensure_directory_exists(directory):
    """
    Creates the specified directory if it does not exist.
    
    :param directory: Path to the directory.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(filename):
    """
    Sanitizes a filename by removing or replacing invalid characters.
    
    :param filename: Original filename.
    :return: Sanitized filename.
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def validate_url(url):
    """
    Validates if the provided string is a valid URL.
    
    :param url: URL string to validate.
    :return: True if valid, False otherwise.
    """
    return url.startswith("http://") or url.startswith("https://")
