import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading

# Permite rodar este arquivo diretamente (python Downloadium/gui/main.py)
# sem exigir instalação do pacote no ambiente.
if __package__ is None or __package__ == "":
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

from Downloadium.backend.downloader import download_thumbnail, download_subtitles
from Downloadium.backend.download_manager import DownloadManager

def start_video_download():
    url = url_entry.get()
    quality = quality_var.get()

    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return

    progress_var.set(0)
    status_var.set("Iniciando...")

    def callback(status: str, percent: float | None = None):
        def update_ui():
            status_var.set(status)
            if percent is not None:
                progress_var.set(percent)

        app.after(0, update_ui)

    def task():
        manager = DownloadManager(output_path="videos", quality=quality, video_format="mp4")

        try:
            total = manager.fetch_metadata(url)
            app.after(0, lambda: status_var.set(f"Video 0 of {total} | Status: Downloading"))
        except Exception:
            pass

        message = manager.download(url, callback)
        app.after(0, lambda: messagebox.showinfo("Resultado", message))

    threading.Thread(target=task, daemon=True).start()

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

# Progresso e status
status_var = tk.StringVar(value="Pronto")
progress_var = tk.DoubleVar(value=0.0)
ttk.Progressbar(app, variable=progress_var, maximum=100).pack(fill="x", padx=10, pady=(0, 5))
tk.Label(app, textvariable=status_var).pack(pady=(0, 10))

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