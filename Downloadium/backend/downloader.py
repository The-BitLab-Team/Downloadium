import os
from yt_dlp import YoutubeDL

def download_video(url, output_path='videos', quality='best'):
    """Downloads a YouTube video based on the provided URL.

    Args:
        url (str): The URL of the video to download.
        output_path (str): Directory where the downloaded file will be saved.
        quality (str): Quality of the video (e.g., 'best', 'worst', specific resolutions like '720p').

    Returns:
        str: The path to the downloaded video file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Set options for yt-dlp
        options = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': quality
        }

        with YoutubeDL(options) as ydl:
            ydl.download([url])

        return f"Video downloaded successfully to {output_path}"

    except Exception as e:
        return f"Error downloading video: {str(e)}"

def download_thumbnail(url, output_path='thumbnails'):
    """Downloads the thumbnail of a YouTube video.

    Args:
        url (str): The URL of the video whose thumbnail is to be downloaded.
        output_path (str): Directory where the thumbnail will be saved.

    Returns:
        str: The path to the downloaded thumbnail file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Get video metadata
        options = {'skip_download': True, 'quiet': True}
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        thumbnail_url = info.get('thumbnail')
        if not thumbnail_url:
            return "No thumbnail found for this video."

        response = requests.get(thumbnail_url)
        response.raise_for_status()

        file_path = os.path.join(output_path, f"{info['title']}_thumbnail.jpg")
        with open(file_path, 'wb') as f:
            f.write(response.content)

        return f"Thumbnail downloaded successfully to {file_path}"

    except Exception as e:
        return f"Error downloading thumbnail: {str(e)}"

def download_subtitles(url, output_path='subtitles', language='en'):
    """Downloads subtitles for a YouTube video in the specified language.

    Args:
        url (str): The URL of the video whose subtitles are to be downloaded.
        output_path (str): Directory where the subtitle file will be saved.
        language (str): Language code of the subtitles to download (e.g., 'en', 'es').

    Returns:
        str: The path to the downloaded subtitle file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Set options for yt-dlp
        options = {
            'skip_download': True,
            'writesubtitles': True,
            'subtitleslangs': [language],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        }

        with YoutubeDL(options) as ydl:
            ydl.download([url])

        return f"Subtitles downloaded successfully to {output_path}"

    except Exception as e:
        return f"Error downloading subtitles: {str(e)}"
