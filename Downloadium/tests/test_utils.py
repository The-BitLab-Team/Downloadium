import unittest
from utils import ensure_directory_exists, sanitize_filename, validate_url
import os

class TestUtils(unittest.TestCase):

    def test_ensure_directory_exists(self):
        test_dir = "test_directory"
        
        # Ensure directory does not exist initially
        if os.path.exists(test_dir):
            os.rmdir(test_dir)
        
        ensure_directory_exists(test_dir)
        self.assertTrue(os.path.exists(test_dir))

        # Clean up
        os.rmdir(test_dir)

    def test_sanitize_filename(self):
        test_cases = {
            "valid_filename": "valid_filename",
            "inva|lid:name?": "inva_lid_name_",
            "path/to\\file": "path_to__file",
            "*file*": "_file_",
        }

        for original, expected in test_cases.items():
            self.assertEqual(sanitize_filename(original), expected)

    def test_validate_url(self):
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://www.example.com/path/to/resource",
        ]

        invalid_urls = [
            "ftp://example.com",
            "example.com",
            "www.example.com",
        ]

        for url in valid_urls:
            self.assertTrue(validate_url(url))

        for url in invalid_urls:
            self.assertFalse(validate_url(url))

if __name__ == "__main__":
    unittest.main()
