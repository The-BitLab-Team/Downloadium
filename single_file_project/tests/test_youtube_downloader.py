import unittest
from unittest.mock import patch, MagicMock
from downloadium import sanitize_filename, validate_url, fetch_video_formats

class TestYoutubeDownloader(unittest.TestCase):

    def test_sanitize_filename(self):
        filename = "invalido:arquivo|teste*"
        sanitized = sanitize_filename(filename)
        self.assertEqual(sanitized, "invalido_arquivo_teste_")

    def test_validate_url(self):
        valid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        invalid_url = "ftp://example.com"
        self.assertTrue(validate_url(valid_url))
        self.assertFalse(validate_url(invalid_url))

    @patch('youtube_downloader_gui.YoutubeDL')
    def test_fetch_video_formats(self, mock_yt_dlp):
        # Mocking yt-dlp response
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'formats': [
                {'format_id': '1', 'format_note': '1080p', 'ext': 'mp4'},
                {'format_id': '2', 'format_note': '720p', 'ext': 'mkv'},
                {'format_id': '3', 'format_note': '480p', 'ext': 'webm'},
            ]
        }
        mock_yt_dlp.return_value = mock_instance

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        formats = fetch_video_formats(url)

        expected_formats = [
            {'format_id': '1', 'resolution': '1080p', 'ext': 'mp4'},
            {'format_id': '2', 'resolution': '720p', 'ext': 'mkv'},
        ]
        self.assertEqual(formats, expected_formats)

if __name__ == "__main__":
    unittest.main()
