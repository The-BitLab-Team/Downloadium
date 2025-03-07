import os
import requests
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from yt_dlp import YoutubeDL
import re
from PIL import Image, ImageTk
from io import BytesIO

class DownloadiumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Downloadium")

        self.download_directory = os.getcwd()
        self.progress_var = tk.DoubleVar()
        self.quality_var = tk.StringVar(value="best")
        self.language_var = tk.StringVar(value="en")
        self.resolution_var = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        url_frame = ttk.LabelFrame(self.root, text="URL do Vídeo")
        url_frame.pack(fill="x", padx=10, pady=5)

        directory_frame = ttk.LabelFrame(self.root, text="Configurações")
        directory_frame.pack(fill="x", padx=10, pady=5)

        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill="x", padx=10, pady=5)

        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(url_frame, text="Insira a URL:").pack(side="left", padx=5, pady=5)
        
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side="left", padx=5, pady=5)
        self.url_entry.bind("<KeyRelease>", self.on_url_change)  # Monitora mudanças na URL

        ttk.Button(url_frame, text="Carregar", command=self.load_resolutions).pack(side="left", padx=5, pady=5)

        ttk.Label(directory_frame, text="Diretório de Download:").pack(side="left", padx=5, pady=5)
        self.directory_label = ttk.Label(directory_frame, text=self.download_directory)
        self.directory_label.pack(side="left", padx=5, pady=5)
        ttk.Button(directory_frame, text="Selecionar", command=self.select_directory).pack(side="right", padx=5, pady=5)

        ttk.Label(directory_frame, text="Resolução:").pack(side="left", padx=5, pady=5)
        self.resolution_combobox = ttk.Combobox(directory_frame, textvariable=self.resolution_var, state="readonly")
        self.resolution_combobox.pack(side="left", padx=5, pady=5)

        self.thumbnail_label = ttk.Label(directory_frame)
        self.thumbnail_label.pack(side="left", padx=5, pady=5)

        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        progress_bar.pack(fill="x", padx=5, pady=5)
        self.status_label = ttk.Label(progress_frame, text="Pronto para iniciar!")
        self.status_label.pack(pady=5)

        ttk.Button(action_frame, text="Baixar Vídeo", command=self.start_video_download).pack(side="left", padx=5, pady=5)
        ttk.Button(action_frame, text="Baixar Thumbnail", command=self.start_thumbnail_download).pack(side="left", padx=5, pady=5)
        ttk.Button(action_frame, text="Baixar Legendas", command=self.start_subtitle_download).pack(side="left", padx=5, pady=5)

        self.url_update_job = None  # Variável para evitar múltiplas chamadas seguidas

        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.geometry("")

    def on_url_change(self, event):
        """ Aguarda 1 segundo após o usuário parar de digitar antes de carregar os dados. """
        if self.url_update_job:
            self.root.after_cancel(self.url_update_job)  # Cancela o carregamento anterior se ainda estiver pendente
        self.url_update_job = self.root.after(1000, self.load_resolutions)

    def select_directory(self):
        self.download_directory = filedialog.askdirectory()
        if self.download_directory:
            self.directory_label.config(text=f"Diretório: {self.download_directory}")

    def load_resolutions(self):
        url = self.url_entry.get()
        if not validate_url(url):
            messagebox.showerror("Erro", "Por favor, insira uma URL válida.")
            return

        try:
            with YoutubeDL({'skip_download': True, 'nocolor': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                resolutions = [f"{f.get('format_note')} ({f.get('format_id')}) - {f.get('ext')}/{f.get('acodec')}" for f in formats if f.get('vcodec') != 'none']
                self.resolution_var.set(resolutions[0] if resolutions else "N/A")
                self.resolution_combobox['values'] = resolutions

                # Load thumbnail
                thumbnail_url = info.get('thumbnail')
                if thumbnail_url:
                    response = requests.get(thumbnail_url)
                    image_data = response.content
                    image = Image.open(BytesIO(image_data))
                    image.thumbnail((100, 100))
                    self.thumbnail_image = ImageTk.PhotoImage(image)
                    self.thumbnail_label.config(image=self.thumbnail_image)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar resoluções: {str(e)}")

    def start_video_download(self):
        url = self.url_entry.get()
        resolution = self.resolution_var.get().split('(')[-1].split(')')[0]
        if not url:
            messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
            return
        self.progress_var.set(0)
        self.status_label.config(text="Iniciando download...")
        message = download_video(url, self.download_directory, resolution, self.progress_hook)
        messagebox.showinfo("Resultado", message)

    def start_thumbnail_download(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
            return
        self.progress_var.set(0)
        self.status_label.config(text="Iniciando download...")
        message = download_thumbnail(url, self.download_directory)
        messagebox.showinfo("Resultado", message)

    def start_subtitle_download(self):
        url = self.url_entry.get()
        language = self.language_var.get()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
            return
        self.progress_var.set(0)
        self.status_label.config(text="Iniciando download...")
        message = download_subtitles(url, self.download_directory, language)
        messagebox.showinfo("Resultado", message)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            progress_str = re.sub(r'\x1b\[[0-9;]*m', '', d['_percent_str'])
            progress = float(progress_str.strip('%'))
            self.progress_var.set(progress)
            self.status_label.config(text=f"Baixando... {progress_str} | {d['_speed_str']} | ETA: {d['_eta_str']}")
        elif d['status'] == 'finished':
            self.status_label.config(text="Download concluído!")

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(filename):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def validate_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// ou https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domínio...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...ou endereço IP
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...ou endereço IPv6
        r'(?::\d+)?'  # porta opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def download_video(url, output_path, quality, progress_hook):
    try:
        ensure_directory_exists(output_path)
        options = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': f'{quality}+bestaudio/best',
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'nocolor': True
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
            'nocolor': True
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return f"Legendas baixadas com sucesso em: {output_path}"
    except Exception as e:
        return f"Erro ao baixar legendas: {str(e)}"

if __name__ == "__main__":
    root = tk.Tk()
    app = DownloadiumApp(root)
    root.mainloop()