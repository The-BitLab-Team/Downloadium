import os
import requests
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from yt_dlp import YoutubeDL

# Funções utilitárias
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(filename):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def validate_url(url):
    return url.startswith("http://") or url.startswith("https://")

# Funções de download
def download_video(url, output_path='videos', quality='best'):
    try:
        ensure_directory_exists(output_path)
        options = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': quality,
            'progress_hooks': [progress_hook]
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return f"Video downloaded successfully to {output_path}"
    except Exception as e:
        return f"Error downloading video: {str(e)}"

def download_thumbnail(url, output_path='thumbnails'):
    try:
        ensure_directory_exists(output_path)
        ydl_opts = {'skip_download': True, 'writesubtitles': False, 'writeautomaticsub': False}
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            thumbnail_url = info_dict.get('thumbnail')
        response = requests.get(thumbnail_url, stream=True)
        response.raise_for_status()
        filename = sanitize_filename(info_dict.get('title', 'thumbnail')) + '.jpg'
        thumbnail_path = os.path.join(output_path, filename)
        total_length = int(response.headers.get('content-length'))
        with open(thumbnail_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
                update_progress(len(chunk), total_length)
        return f"Thumbnail downloaded successfully to {thumbnail_path}"
    except Exception as e:
        return f"Error downloading thumbnail: {str(e)}"

def download_subtitles(url, output_path='subtitles', language='en'):
    try:
        ensure_directory_exists(output_path)
        options = {
            'writesubtitles': True,
            'subtitleslangs': [language],
            'skip_download': True,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook]
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return f"Subtitles downloaded successfully to {output_path}"
    except Exception as e:
        return f"Error downloading subtitles: {str(e)}"

def progress_hook(d):
    if d['status'] == 'downloading':
        p = d['_percent_str'].strip().replace('\x1b[0;94m', '').replace('\x1b[0m', '')
        progress_var.set(float(p.strip('%')))
        app.update_idletasks()

def update_progress(chunk_size, total_size):
    progress_var.set(progress_var.get() + (chunk_size / total_size) * 100)
    app.update_idletasks()

# Funções da interface gráfica
def select_directory():
    global download_directory
    download_directory = filedialog.askdirectory()
    if download_directory:
        directory_label.config(text=f"Diretório selecionado: {download_directory}")

def update_quality_menu(url):
    try:
        ydl_opts = {'format': 'best'}
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            resolutions = sorted(set(f"{f['format_note']} ({f['format_id']})" for f in formats if 'format_note' in f))
            quality_var.set(resolutions[0] if resolutions else 'best')
            quality_menu['menu'].delete(0, 'end')
            for res in resolutions:
                quality_menu['menu'].add_command(label=res, command=tk._setit(quality_var, res))
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao obter resoluções: {str(e)}")

def start_video_download():
    url = url_entry.get()
    quality = quality_var.get().split('(')[-1].strip(')')
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    progress_var.set(0)
    message = download_video(url, output_path=download_directory, quality=quality)
    messagebox.showinfo("Resultado", message)

def start_thumbnail_download():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    progress_var.set(0)
    message = download_thumbnail(url, output_path=download_directory)
    messagebox.showinfo("Resultado", message)

def start_subtitle_download():
    url = url_entry.get()
    language = language_var.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    progress_var.set(0)
    message = download_subtitles(url, output_path=download_directory, language=language)
    messagebox.showinfo("Resultado", message)

def fetch_resolutions():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    update_quality_menu(url)

# Configurar a interface gráfica
app = tk.Tk()
app.title("Downloadium")

# Variável para armazenar o diretório de download
download_directory = ''

# Entrada para a URL
tk.Label(app, text="URL do vídeo:").pack(pady=5)
url_entry = tk.Entry(app, width=50)
url_entry.pack(pady=5)

# Botão para buscar resoluções
fetch_resolutions_button = tk.Button(app, text="Buscar Resoluções", command=fetch_resolutions)
fetch_resolutions_button.pack(pady=5)

# Seleção de qualidade
tk.Label(app, text="Qualidade do vídeo:").pack(pady=5)
quality_var = tk.StringVar(value="best")
quality_menu = tk.OptionMenu(app, quality_var, "best")
quality_menu.pack(pady=5)

# Botão para selecionar diretório
select_directory_button = tk.Button(app, text="Selecionar Diretório", command=select_directory)
select_directory_button.pack(pady=10)

# Label para mostrar o diretório selecionado
directory_label = tk.Label(app, text="Nenhum diretório selecionado")
directory_label.pack(pady=5)

# Barra de progresso
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(app, variable=progress_var, maximum=100)
progress_bar.pack(pady=10, fill=tk.X)

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