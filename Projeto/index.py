import tkinter as tk
from tkinter import messagebox
from pytube import YouTube
import os

def download_video():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return

    try:
        yt = YouTube(url)
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        resolutions = [stream.resolution for stream in streams]
        
        if not resolutions:
            messagebox.showerror("Erro", "Não foram encontradas resoluções disponíveis para este vídeo.")
            return
        
        resolution = resolution_var.get()
        if resolution not in resolutions:
            messagebox.showerror("Erro", "Resolução selecionada não disponível.")
            return
        
        video = streams.filter(res=resolution).first()
        video.download(output_path='videos')
        
        # Download thumbnail
        thumbnail_url = yt.thumbnail_url
        thumbnail_data = requests.get(thumbnail_url).content
        with open(os.path.join('videos', f'{yt.title}_thumbnail.jpg'), 'wb') as f:
            f.write(thumbnail_data)
        
        # Download captions
        if yt.captions:
            caption = yt.captions.get_by_language_code('en')
            if caption:
                caption.download(title=yt.title, output_path='videos')
        
        messagebox.showinfo("Sucesso", "Download concluído com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

def update_resolutions():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return

    try:
        yt = YouTube(url)
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        resolutions = [stream.resolution for stream in streams]
        
        resolution_menu['menu'].delete(0, 'end')
        for res in resolutions:
            resolution_menu['menu'].add_command(label=res, command=tk._setit(resolution_var, res))
        
        if resolutions:
            resolution_var.set(resolutions[0])
        else:
            resolution_var.set('')
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

app = tk.Tk()
app.title("YouTube Downloader")

tk.Label(app, text="URL do vídeo:").pack(pady=5)
url_entry = tk.Entry(app, width=50)
url_entry.pack(pady=5)

resolution_var = tk.StringVar(app)
resolution_menu = tk.OptionMenu(app, resolution_var, '')
resolution_menu.pack(pady=5)

update_button = tk.Button(app, text="Atualizar Resoluções", command=update_resolutions)
update_button.pack(pady=5)

download_button = tk.Button(app, text="Baixar Vídeo", command=download_video)
download_button.pack(pady=20)

app.mainloop()