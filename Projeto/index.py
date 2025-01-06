import tkinter as tk
from tkinter import messagebox
from pytube import YouTube
import os
import requests

def download_video():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return

    try:
        yt = YouTube(url)
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        resolution = resolution_var.get()

        # Verifica se a resolução está disponível
        video = streams.filter(res=resolution).first()
        if not video:
            messagebox.showerror("Erro", "Resolução selecionada não disponível.")
            return

        # Cria pasta de downloads se não existir
        os.makedirs('videos', exist_ok=True)

        # Download do vídeo
        video.download(output_path='videos')

        # Download da thumbnail
        thumbnail_url = yt.thumbnail_url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(thumbnail_url, headers=headers)

        if response.status_code == 200:  # Verifica se a resposta foi bem-sucedida
            with open(os.path.join('videos', f'{yt.title}_thumbnail.jpg'), 'wb') as f:
                f.write(response.content)
        else:
            messagebox.showerror("Erro", f"Falha ao baixar a thumbnail. Código HTTP: {response.status_code}")

        # Download das legendas, se disponíveis
        if yt.captions:
            caption = yt.captions.get_by_language_code('en')
            if caption:
                caption_file = caption.generate_srt_captions()
                with open(os.path.join('videos', f'{yt.title}.srt'), 'w', encoding='utf-8') as f:
                    f.write(caption_file)

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

        # Atualiza o menu de resoluções
        resolution_menu['menu'].delete(0, 'end')
        for res in resolutions:
            resolution_menu['menu'].add_command(label=res, command=tk._setit(resolution_var, res))

        if resolutions:
            resolution_var.set(resolutions[0])
        else:
            resolution_var.set('')
            messagebox.showwarning("Aviso", "Nenhuma resolução disponível.")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

# Configurações da interface gráfica
app = tk.Tk()
app.title("Downloadium")

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
