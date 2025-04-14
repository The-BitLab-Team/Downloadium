import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# Funções auxiliares
def get_resolutions(url, cookies=None):
    options = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'nocolor': True
    }
    if cookies:
        options['cookiefile'] = cookies
    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [info])
            resolutions = sorted(set(f.get('format_note') for f in formats if f.get('vcodec') != 'none'))
            thumbnail = info.get('thumbnail')
            return [r for r in resolutions if r], thumbnail
    except DownloadError:
        return [], None

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_video(url, resolution, output_path, progress_hook=None, cookies=None, video_format="mp4"):
    try:
        ensure_directory_exists(output_path)
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': f'bestvideo[format_note={resolution}]+bestaudio/best[ext={video_format}]',
            'merge_output_format': video_format,
            'progress_hooks': [progress_hook] if progress_hook else [],
            'noplaylist': True,
            'nocolor': True
        }
        if cookies:
            ydl_opts['cookiefile'] = cookies
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "Download finalizado com sucesso!"
    except Exception as e:
        return f"Erro no download: {str(e)}"

def download_thumbnail(url, output_path):
    try:
        ensure_directory_exists(output_path)
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        filename = os.path.join(output_path, os.path.basename(url))
        img.save(filename)
        return f"Thumbnail salva em: {filename}"
    except Exception as e:
        return f"Erro ao baixar thumbnail: {str(e)}"

def download_subtitles(url, output_path, language="en"):
    try:
        ensure_directory_exists(output_path)
        options = {
            'writesubtitles': True,
            'subtitleslangs': [language],
            'skip_download': True,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'nocolor': True
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return f"Legenda ({language}) baixada com sucesso!"
    except Exception as e:
        return f"Erro ao baixar legenda: {str(e)}"

# Interface
class DownloadiumApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Downloadium")
        self.geometry("600x500")

        self.url_var = tk.StringVar()
        self.output_path_var = tk.StringVar(value=os.path.expanduser("~"))
        self.resolution_var = tk.StringVar()
        self.format_var = tk.StringVar(value="mp4")
        self.cookie_path_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()

        self.thumbnail_url = None
        self.thumbnail_image = None

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="URL do vídeo:").pack(anchor=tk.W)
        url_entry = ttk.Entry(frame, textvariable=self.url_var, width=70)
        url_entry.pack()

        ttk.Label(frame, text="Caminho de saída:").pack(anchor=tk.W, pady=(10, 0))
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill=tk.X)
        ttk.Entry(path_frame, textvariable=self.output_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="...", command=self.choose_output_path).pack(side=tk.LEFT)

        ttk.Label(frame, text="Resolução:").pack(anchor=tk.W, pady=(10, 0))
        self.resolution_cb = ttk.Combobox(frame, textvariable=self.resolution_var, state="readonly")
        self.resolution_cb.pack()

        ttk.Button(frame, text="Carregar Resoluções", command=self.load_resolutions).pack(pady=5)

        # Seletor de formato
        ttk.Label(frame, text="Formato de vídeo:").pack(anchor=tk.W, pady=(10, 0))
        format_cb = ttk.Combobox(frame, textvariable=self.format_var, values=["mp4", "mkv", "webm"], state="readonly")
        format_cb.pack()
        format_cb.current(0)

        self.thumbnail_label = ttk.Label(frame)
        self.thumbnail_label.pack(pady=10)

        ttk.Label(frame, text="Cookies (opcional):").pack(anchor=tk.W)
        cookie_frame = ttk.Frame(frame)
        cookie_frame.pack(fill=tk.X)
        ttk.Entry(cookie_frame, textvariable=self.cookie_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(cookie_frame, text="...", command=self.choose_cookie_path).pack(side=tk.LEFT)

        progress_frame = ttk.Frame(frame)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Baixar Vídeo", command=self.download_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Baixar Thumbnail", command=self.download_thumbnail).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Baixar Legenda", command=self.download_subtitle).pack(side=tk.LEFT, padx=5)

    def choose_output_path(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path_var.set(path)

    def choose_cookie_path(self):
        file = filedialog.askopenfilename()
        if file:
            self.cookie_path_var.set(file)

    def load_resolutions(self):
        url = self.url_var.get()
        cookies = self.cookie_path_var.get() or None
        resolutions, thumbnail = get_resolutions(url, cookies)
        self.resolution_cb['values'] = resolutions
        if resolutions:
            self.resolution_cb.current(0)
        if thumbnail:
            self.thumbnail_url = thumbnail
            try:
                response = requests.get(thumbnail)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
                image.thumbnail((100, 100))
                self.thumbnail_image = ImageTk.PhotoImage(image)
                self.thumbnail_label.config(image=self.thumbnail_image, text="")
            except:
                self.thumbnail_label.config(text="Erro ao carregar imagem")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = downloaded_bytes / total_bytes * 100
                self.progress_var.set(percent)
                self.update_idletasks()
        elif d['status'] == 'finished':
            self.progress_var.set(100)
            self.update_idletasks()

    def download_video(self):
        result = download_video(
            self.url_var.get(),
            self.resolution_var.get(),
            self.output_path_var.get(),
            progress_hook=self.progress_hook,
            cookies=self.cookie_path_var.get() or None,
            video_format=self.format_var.get()
        )
        messagebox.showinfo("Download", result)

    def download_thumbnail(self):
        if not self.thumbnail_url:
            messagebox.showwarning("Aviso", "Nenhuma thumbnail carregada.")
            return
        result = download_thumbnail(self.thumbnail_url, self.output_path_var.get())
        messagebox.showinfo("Download", result)

    def download_subtitle(self):
        result = download_subtitles(
            self.url_var.get(),
            self.output_path_var.get(),
            language="en"
        )
        messagebox.showinfo("Legenda", result)

if __name__ == '__main__':
    app = DownloadiumApp()
    app.mainloop()
