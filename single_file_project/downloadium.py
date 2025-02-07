import os
import requests
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from yt_dlp import YoutubeDL
import re

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
def download_video(url, output_path, quality):
    try:
        ensure_directory_exists(output_path)
        options = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': f'{quality}+bestaudio/best',
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'nocolor': True  # Desativa a coloração ANSI
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return f"Vídeo baixado com sucesso em: {output_path}"
    except Exception as e:
        return f"Erro ao baixar vídeo: {str(e)}"

def download_thumbnail(url, output_path):
    try:
        ensure_directory_exists(output_path)
        with YoutubeDL({'skip_download': True, 'nocolor': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail_url = info['thumbnail']
            title = sanitize_filename(info.get('title', 'thumbnail'))
        
        response = requests.get(thumbnail_url, stream=True)
        response.raise_for_status()
        file_path = os.path.join(output_path, f"{title}.jpg")
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        
        return f"Thumbnail baixada com sucesso em: {file_path}"
    except Exception as e:
        return f"Erro ao baixar thumbnail: {str(e)}"

def download_subtitles(url, output_path, language):
    try:
        ensure_directory_exists(output_path)
        options = {
            'writesubtitles': True,
            'subtitleslangs': [language],
            'skip_download': True,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'nocolor': True  # Desativa a coloração ANSI
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return f"Legendas baixadas com sucesso em: {output_path}"
    except Exception as e:
        return f"Erro ao baixar legendas: {str(e)}"

def progress_hook(d):
    if d['status'] == 'downloading':
        progress_str = re.sub(r'\x1b\[[0-9;]*m', '', d['_percent_str'])  # Remove caracteres de escape ANSI
        progress = float(progress_str.strip('%'))
        progress_var.set(progress)
        status_label.config(text=f"Baixando... {progress_str} | {d['_speed_str']} | ETA: {d['_eta_str']}")
    elif d['status'] == 'finished':
        status_label.config(text="Download concluído!")

# Funções da interface gráfica
def select_directory():
    global download_directory
    download_directory = filedialog.askdirectory()
    if download_directory:
        directory_label.config(text=f"Diretório: {download_directory}")

def load_resolutions():
    url = url_entry.get()
    if not validate_url(url):
        messagebox.showerror("Erro", "Por favor, insira uma URL válida.")
        return
    
    try:
        with YoutubeDL({'skip_download': True, 'nocolor': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            resolutions = []
            for f in formats:
                if f.get('vcodec') != 'none':  # Apenas formatos de vídeo
                    resolution = f.get('format_note')
                    ext = f.get('ext')
                    if resolution and ext:
                        resolutions.append(f"{resolution} ({ext})")
            resolution_var.set(resolutions[0] if resolutions else "N/A")
            resolution_combobox['values'] = resolutions
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar resoluções: {str(e)}")

def start_video_download():
    url = url_entry.get()
    quality = resolution_var.get().split(' ')[0]  # Pega a resolução selecionada
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    progress_var.set(0)
    status_label.config(text="Iniciando download...")
    message = download_video(url, download_directory, quality)
    messagebox.showinfo("Resultado", message)

def start_thumbnail_download():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    progress_var.set(0)
    status_label.config(text="Iniciando download...")
    message = download_thumbnail(url, download_directory)
    messagebox.showinfo("Resultado", message)

def start_subtitle_download():
    url = url_entry.get()
    language = language_var.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    progress_var.set(0)
    status_label.config(text="Iniciando download...")
    message = download_subtitles(url, download_directory, language)
    messagebox.showinfo("Resultado", message)

# Configurar a interface gráfica
app = tk.Tk()
app.title("Downloadium")
app.geometry("600x600")

# Variáveis globais
download_directory = os.getcwd()
progress_var = tk.DoubleVar()
quality_var = tk.StringVar(value="best")
language_var = tk.StringVar(value="en")
resolution_var = tk.StringVar()

# Frames
url_frame = ttk.LabelFrame(app, text="URL do Vídeo")
url_frame.pack(fill="x", padx=10, pady=5)

directory_frame = ttk.LabelFrame(app, text="Configurações")
directory_frame.pack(fill="x", padx=10, pady=5)

progress_frame = ttk.Frame(app)
progress_frame.pack(fill="x", padx=10, pady=5)

action_frame = ttk.Frame(app)
action_frame.pack(fill="x", padx=10, pady=5)

# Entrada para URL
ttk.Label(url_frame, text="Insira a URL:").pack(side="left", padx=5, pady=5)
url_entry = ttk.Entry(url_frame, width=50)
url_entry.pack(side="left", padx=5, pady=5)
ttk.Button(url_frame, text="Carregar", command=load_resolutions).pack(side="left", padx=5, pady=5)

# Diretório
ttk.Label(directory_frame, text="Diretório de Download:").pack(side="left", padx=5, pady=5)
directory_label = ttk.Label(directory_frame, text=download_directory)
directory_label.pack(side="left", padx=5, pady=5)
ttk.Button(directory_frame, text="Selecionar", command=select_directory).pack(side="right", padx=5, pady=5)

# Seleção de Resolução
ttk.Label(directory_frame, text="Resolução:").pack(side="left", padx=5, pady=5)
resolution_combobox = ttk.Combobox(directory_frame, textvariable=resolution_var, state="readonly")
resolution_combobox.pack(side="left", padx=5, pady=5)

# Barra de progresso
progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=5, pady=5)
status_label = ttk.Label(progress_frame, text="Pronto para iniciar!")
status_label.pack(pady=5)

# Botões de Ação
ttk.Button(action_frame, text="Baixar Vídeo", command=start_video_download).pack(side="left", padx=5, pady=5)
ttk.Button(action_frame, text="Baixar Thumbnail", command=start_thumbnail_download).pack(side="left", padx=5, pady=5)
ttk.Button(action_frame, text="Baixar Legendas", command=start_subtitle_download).pack(side="left", padx=5, pady=5)

app.mainloop()