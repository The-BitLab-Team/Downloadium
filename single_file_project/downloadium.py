import os
import requests
import tkinter as tk
from tkinter import messagebox
from yt_dlp import YoutubeDL

# Funções utilitárias
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

# Funções de download
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
        ensure_directory_exists(output_path)

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
        ensure_directory_exists(output_path)

        # Get video info
        ydl_opts = {'skip_download': True, 'writesubtitles': False, 'writeautomaticsub': False}
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            thumbnail_url = info_dict.get('thumbnail')

        # Download the thumbnail
        response = requests.get(thumbnail_url, stream=True)
        response.raise_for_status()

        # Save the thumbnail
        filename = sanitize_filename(info_dict.get('title', 'thumbnail')) + '.jpg'
        thumbnail_path = os.path.join(output_path, filename)
        with open(thumbnail_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        return f"Thumbnail downloaded successfully to {thumbnail_path}"

    except Exception as e:
        return f"Error downloading thumbnail: {str(e)}"

def download_subtitles(url, output_path='subtitles', language='en'):
    """Downloads subtitles for a YouTube video.

    Args:
        url (str): The URL of the video whose subtitles are to be downloaded.
        output_path (str): Directory where the subtitles will be saved.
        language (str): Language of the subtitles (default is 'en').

    Returns:
        str: The path to the downloaded subtitles file.
    """
    try:
        # Ensure the output directory exists
        ensure_directory_exists(output_path)

        # Set options for yt-dlp
        options = {
            'writesubtitles': True,
            'subtitleslangs': [language],
            'skip_download': True,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s')
        }

        with YoutubeDL(options) as ydl:
            ydl.download([url])

        return f"Subtitles downloaded successfully to {output_path}"

    except Exception as e:
        return f"Error downloading subtitles: {str(e)}"

# Funções da interface gráfica
def start_video_download():
    url = url_entry.get()
    quality = quality_var.get()

    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return

    message = download_video(url, quality=quality)
    messagebox.showinfo("Resultado", message)

def start_thumbnail_download():
    url = url_entry.get()

    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return

    message = download_thumbnail(url)
    messagebox.showinfo("Resultado", message)

def start_subtitle_download():
    url = url_entry.get()
    language = language_var.get()

    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return

    message = download_subtitles(url, language=language)
    messagebox.showinfo("Resultado", message)

# Configurar a interface gráfica
app = tk.Tk()
app.title("Downloadium")

# Entrada para a URL
tk.Label(app, text="URL do vídeo:").pack(pady=5)
url_entry = tk.Entry(app, width=50)
url_entry.pack(pady=5)

# Seleção de qualidade
tk.Label(app, text="Qualidade do vídeo:").pack(pady=5)
quality_var = tk.StringVar(value="best")
quality_menu = tk.OptionMenu(app, quality_var, "best", "worst", "720p", "480p", "360p")
quality_menu.pack(pady=5)

# Botão para baixar vídeo
download_video_button = tk.Button(app, text="Baixar Vídeo", command=start_video_download)
download_video_button.pack(pady=10)

# Botão para baixar thumbnail
download_thumbnail_button = tk.Button(app, text="Baixar Thumbnail", command=start_thumbnail_download)
download_thumbnail_button.pack(pady=10)

# Seleção de idioma para legendas
tk.Label(app, text="Idioma das legendas:").pack(pady=5)
language_var = tk.StringVar(value="en")
language_entry = tk.Entry(app, textvariable=language_var)
language_entry.pack(pady=5)

# Botão para baixar legendas
download_subtitles_button = tk.Button(app, text="Baixar Legendas", command=start_subtitle_download)
download_subtitles_button.pack(pady=10)

app.mainloop()