import tkinter as tk
from tkinter import messagebox
from Downloadium.backend.downloader import download_video, download_thumbnail, download_subtitles

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
