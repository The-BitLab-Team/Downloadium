import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

# --- Funções auxiliares ---

def get_resolutions(url, cookies_file=None):
    """
    Obtém as resoluções disponíveis e o URL da thumbnail de um vídeo.
    Args:
        url (str): O URL do vídeo.
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
    Returns:
        tuple: Uma tupla contendo uma lista de resoluções (str) e o URL da thumbnail (str) ou None em caso de erro.
    """
    options: dict[str, bool | int] = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'nocolor': True,
        'cachedir': False, # Evita problemas de cache
        'retries': 5 # Tenta algumas vezes em caso de problemas de rede transitórios
    }
    if cookies_file and os.path.exists(cookies_file):
        options['cookiefile'] = cookies_file
    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return [], None, "Não foi possível extrair informações do vídeo."

            formats = info.get('formats') or [info] # Fallback para o próprio info se 'formats' estiver ausente
            
            # Filtra por formatos de vídeo que não são 'none' e têm um 'format_note'
            # e os ordena. Converte notas de resolução para inteiros para uma ordenação adequada, se possível
            resolutions_with_quality = []
            for f in formats:
                format_note = f.get('format_note')
                vcodec = f.get('vcodec')
                if vcodec != 'none' and format_note:
                    # Tenta analisar a resolução (ex: '1080p' -> 1080) para uma melhor ordenação
                    try:
                        height = int("".join(filter(str.isdigit, format_note)))
                        resolutions_with_quality.append((height, format_note))
                    except ValueError:
                        resolutions_with_quality.append((0, format_note)) # Fallback se não for analisável

            # Ordena por altura (decrescente) e depois pela string original
            # O set é para remover duplicatas mantendo a ordem para os valores já vistos
            unique_resolutions = sorted(list(set(r[1] for r in resolutions_with_quality)), 
                                        key=lambda x: (int("".join(filter(str.isdigit, x))) if any(char.isdigit() for char in x) else 0), 
                                        reverse=True)
            # Adiciona uma opção "Melhor" no topo para o yt-dlp escolher a melhor qualidade automaticamente
            final_resolutions = ["Melhor"] + unique_resolutions if unique_resolutions else []

            thumbnail = info.get('thumbnail')
            return final_resolutions, thumbnail, None
    except ExtractorError as e:
        return [], None, f"Erro ao extrair informações do vídeo: {e}"
    except DownloadError as e: # Captura erros de download específicos do yt_dlp
        return [], None, f"Erro de download do yt-dlp: {e}"
    except Exception as e:
        return [], None, f"Erro inesperado ao obter resoluções: {e}"

def ensure_directory_exists(path):
    """Garante que o diretório especificado exista."""
    if not os.path.exists(path):
        os.makedirs(path)

def download_video(url, resolution, output_path, progress_hook=None, cookies_file=None, video_format="mp4"):
    """
    Baixa um vídeo com a resolução e formato especificados.
    Args:
        url (str): O URL do vídeo.
        resolution (str): A resolução desejada (ex: '1080p' ou 'Melhor').
        output_path (str): O diretório de saída.
        progress_hook (function, optional): Função de callback para progresso.
        cookies_file (str, optional): Caminho para o arquivo de cookies.
        video_format (str, optional): Formato de saída do vídeo (ex: 'mp4').
    Returns:
        str: Mensagem de status do download.
    """
    try:
        if not url:
            return "Erro: URL do vídeo não fornecida."
        if not resolution:
            return "Erro: Resolução não selecionada."
        if not output_path:
            return "Erro: Caminho de saída não fornecido."

        ensure_directory_exists(output_path)
        
        # Determina a string de formato com base na resolução.
        # Se a resolução for 'Melhor', usa 'bestvideo+bestaudio'.
        # Caso contrário, tenta encontrar um 'format_note' específico.
        if resolution.lower() == 'melhor':
            format_string = f'bestvideo+bestaudio/best[ext={video_format}]'
        else:
            # Usa format_note*= para uma correspondência mais flexível,
            # ou bestvideo[height<=...] para resolução numérica se disponível.
            # No momento, mantemos a lógica do usuário para 'format_note'.
            format_string = f'bestvideo[format_note*={resolution}]+bestaudio/best[ext={video_format}]'
        
        ydl_opts: dict[str, bool | int | str | list] = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': format_string,
            'merge_output_format': video_format,
            'progress_hooks': [progress_hook] if progress_hook else [],
            'noplaylist': True,
            'nocolor': True,
            'cachedir': False,
            'retries': 5
        }
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "Download finalizado com sucesso!"
    except DownloadError as e:
        return f"Erro no download (yt-dlp): {str(e)}"
    except Exception as e:
        return f"Erro inesperado no download: {str(e)}"

def download_thumbnail(url, output_path):
    """
    Baixa a thumbnail de um vídeo.
    Args:
        url (str): URL da thumbnail.
        output_path (str): Diretório de saída.
    Returns:
        str: Mensagem de status do download.
    """
    try:
        if not url:
            return "Erro: URL da thumbnail não fornecida."
        if not output_path:
            return "Erro: Caminho de saída não fornecido."
            
        ensure_directory_exists(output_path)
        response = requests.get(url, stream=True, timeout=10) # Usa stream=True para arquivos maiores, adiciona timeout
        response.raise_for_status() # Lança HTTPError para respostas ruins (4xx ou 5xx)
        
        # Extrai o nome do arquivo da URL ou gera um genérico
        filename_from_url = os.path.basename(url.split('?')[0]) # Remove parâmetros de consulta
        if not filename_from_url or '.' not in filename_from_url:
            filename = "thumbnail.jpg" # Nome de arquivo padrão se a URL não fornecer um ou não tiver extensão
        else:
            # Garante que tenha uma extensão de imagem, padroniza para .jpg se nenhuma
            if not any(filename_from_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                filename_from_url += '.jpg'
            filename = filename_from_url
            
        full_path = os.path.join(output_path, filename)
        
        # Salva o conteúdo da imagem diretamente
        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return f"Thumbnail salva em: {full_path}"
    except requests.exceptions.RequestException as e:
        return f"Erro de rede ao baixar thumbnail: {str(e)}"
    except Exception as e:
        return f"Erro inesperado ao baixar thumbnail: {str(e)}"

def download_subtitles(url, output_path, language="en"):
    """
    Baixa as legendas de um vídeo.
    Args:
        url (str): O URL do vídeo.
        output_path (str): O diretório de saída.
        language (str, optional): Idioma da legenda. Defaults to "en".
    Returns:
        str: Mensagem de status do download.
    """
    try:
        if not url:K
            return "Erro: URL do vídeo não fornecida."
        if not output_path:
            return "Erro: Caminho de saída não fornecido."

        ensure_directory_exists(output_path)
        options = {
            'writesubtitles': True,
            'subtitleslangs': [language],
            'skip_download': True, # Apenas extrai informações e escreve legendas
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'nocolor': True,
            'cachedir': False,
            'retries': 5
        }
        with YoutubeDL(options) as ydl:
            # As legendas são escritas durante a extração de informações se writesubtitles for True
            # e subtitleslangs corresponderem às legendas disponíveis.
            info = ydl.extract_info(url, download=False)
            if info:
                # Verifica se há legendas no idioma especificado na informação extraída
                if info.get('requested_subtitles', {}).get(language):
                    return f"Legenda ({language}) baixada com sucesso!"
                else:
                    return f"Legenda ({language}) não disponível para este vídeo."
            else:
                return "Não foi possível encontrar informações para baixar a legenda."
    except DownloadError as e:
        return f"Erro ao baixar legenda (yt-dlp): {str(e)}"
    except Exception as e:
        return f"Erro inesperado ao baixar legenda: {str(e)}"

# --- Interface ---

class DownloadiumApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Downloadium - Seu Baixador de Vídeos")
        self.geometry("650x550") # Janela um pouco maior
        self.resizable(False, False) # Torna a janela não redimensionável para simplicidade

        # Configurações de estilo
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'
        self.style.configure('TFrame', background='#e0e0e0')
        self.style.configure('TLabel', background='#e0e0e0', font=('Inter', 10))
        self.style.configure('TButton', font=('Inter', 10, 'bold'), padding=6)
        self.style.map('TButton',
                       foreground=[('active', 'black'), ('disabled', 'grey')],
                       background=[('active', '#a0a0a0'), ('disabled', '#cccccc')])
        self.style.configure('TEntry', font=('Inter', 10))
        self.style.configure('TCombobox', font=('Inter', 10))
        self.style.configure('TProgressbar', thickness=15)

        # Variáveis
        self.url_var = tk.StringVar()
        # Caminho de saída padrão para a pasta de Downloads do usuário
        self.output_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.resolution_var = tk.StringVar()
        self.format_var = tk.StringVar(value="mp4") # Padrão para mp4
        self.cookie_path_var = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0.0) # Inicializa o progresso para 0
        
        # Mensagem de status inicial, orientando o usuário
        self.status_text_var = tk.StringVar(value="Por favor, insira a URL do vídeo e clique em 'Carregar Resoluções'.")

        self.thumbnail_url = None
        self.thumbnail_image = None # Mantém uma referência para evitar a coleta de lixo

        self.create_widgets()
        # Os botões de download são desativados inicialmente, pois as informações do vídeo (resoluções)
        # ainda não foram carregadas. Eles serão ativados após o sucesso do carregamento de resoluções.
        self.update_download_button_state(False)

    def create_widgets(self):
        """Cria e organiza todos os widgets da interface."""
        # Frame principal
        main_frame = ttk.Frame(self, padding="15 15 15 15", relief="raised")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entrada de URL
        ttk.Label(main_frame, text="URL do vídeo:").pack(anchor=tk.W, pady=(0, 5))
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=80)
        url_entry.pack(fill=tk.X, ipady=3)
        # Associa a tecla Enter ao carregamento de resoluções para conveniência do usuário
        url_entry.bind("<Return>", lambda event: self.load_resolutions_threaded())

        # Caminho de saída
        ttk.Label(main_frame, text="Caminho de saída:").pack(anchor=tk.W, pady=(10, 5))
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X)
        ttk.Entry(path_frame, textvariable=self.output_path_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        ttk.Button(path_frame, text="Procurar Pasta", command=self.choose_output_path).pack(side=tk.LEFT, padx=(5, 0))

        # Resoluções e botão Carregar
        ttk.Label(main_frame, text="Resolução:").pack(anchor=tk.W, pady=(10, 5))
        resolution_frame = ttk.Frame(main_frame)
        resolution_frame.pack(fill=tk.X)
        self.resolution_cb = ttk.Combobox(resolution_frame, textvariable=self.resolution_var, state="readonly", width=30)
        self.resolution_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.resolution_cb.set("Selecione...") # Texto de placeholder inicial
        # Este botão é sempre clicável para iniciar o processo de carregamento de resoluções
        ttk.Button(resolution_frame, text="Carregar Resoluções", command=self.load_resolutions_threaded).pack(side=tk.LEFT, padx=(5, 0))

        # Seletor de formato de vídeo
        ttk.Label(main_frame, text="Formato de vídeo:").pack(anchor=tk.W, pady=(10, 5))
        format_cb = ttk.Combobox(main_frame, textvariable=self.format_var, values=["mp4", "mkv", "webm", "avi", "mov"], state="readonly", width=30)
        format_cb.pack(fill=tk.X, ipady=3)
        format_cb.set("mp4") # Define o valor de exibição padrão

        # Exibição da thumbnail
        self.thumbnail_label = ttk.Label(main_frame, text="Preview da Thumbnail", relief="solid", borderwidth=1, anchor=tk.CENTER)
        # Removido tamanho fixo, usando ipadx/ipady para padding e fill/expand para adaptabilidade
        self.thumbnail_label.pack(pady=15, padx=10, fill=tk.BOTH, expand=False, ipadx=75, ipady=50)

        # Caminho dos Cookies
        ttk.Label(main_frame, text="Arquivo de Cookies (opcional):").pack(anchor=tk.W, pady=(5, 5))
        cookie_frame = ttk.Frame(main_frame)
        cookie_frame.pack(fill=tk.X)
        ttk.Entry(cookie_frame, textvariable=self.cookie_path_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        ttk.Button(cookie_frame, text="Procurar Arquivo", command=self.choose_cookie_path).pack(side=tk.LEFT, padx=(5, 0))

        # Barra de Progresso e Status
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill=tk.X, padx=15, pady=(0, 5))
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_text_var, font=('Inter', 9, 'italic'), foreground='blue')
        self.status_label.pack(anchor=tk.W, pady=(0, 5))

        # Botões de Ação
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        # Referências aos botões para poder habilitar/desabilitar
        self.download_video_btn = ttk.Button(button_frame, text="Baixar Vídeo", command=self.download_video_threaded)
        self.download_video_btn.pack(side=tk.LEFT, padx=10)
        self.download_thumbnail_btn = ttk.Button(button_frame, text="Baixar Thumbnail", command=self.download_thumbnail_threaded)
        self.download_thumbnail_btn.pack(side=tk.LEFT, padx=10)
        self.download_subtitle_btn = ttk.Button(button_frame, text="Baixar Legenda (en)", command=self.download_subtitle_threaded)
        self.download_subtitle_btn.pack(side=tk.LEFT, padx=10)
        self.download_all_btn = ttk.Button(button_frame, text="Download Completo", command=self.download_all_threaded)
        self.download_all_btn.pack(side=tk.LEFT, padx=10)

    def choose_output_path(self):
        """Abre uma caixa de diálogo para escolher o diretório de saída."""
        path = filedialog.askdirectory(initialdir=self.output_path_var.get())
        if path:
            self.output_path_var.set(path)

    def choose_cookie_path(self):
        """Abre uma caixa de diálogo para escolher o arquivo de cookies."""
        file = filedialog.askopenfilename(filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")])
        if file:
            self.cookie_path_var.set(file)

    def update_status(self, message, color='blue'):
        """Atualiza a mensagem de status na interface."""
        self.status_text_var.set(message)
        self.status_label.config(foreground=color)
        self.update_idletasks()

    def update_download_button_state(self, enable=True):
        """Habilita ou desabilita os botões de download."""
        if enable:
            self.download_video_btn.config(state=tk.NORMAL)
            self.download_thumbnail_btn.config(state=tk.NORMAL)
            self.download_subtitle_btn.config(state=tk.NORMAL)
            self.download_all_btn.config(state=tk.NORMAL)
        else:
            self.download_video_btn.config(state=tk.DISABLED)
            self.download_thumbnail_btn.config(state=tk.DISABLED)
            self.download_subtitle_btn.config(state=tk.DISABLED)
            self.download_all_btn.config(state=tk.DISABLED)

    def load_resolutions_threaded(self):
        """Inicia o carregamento de resoluções em uma nova thread."""
        url = self.url_var.get()
        if not url or not url.strip().startswith(('http://', 'https://')):
            messagebox.showwarning("URL Inválida", "Por favor, insira uma URL de vídeo válida.")
            self.update_status("Por favor, insira uma URL válida.", 'red')
            self.resolution_cb['values'] = []
            self.resolution_cb.set("Selecione...")
            self.thumbnail_label.config(image='', text="Preview da Thumbnail")
            self.thumbnail_image = None
            self.update_download_button_state(False) # Garante que os botões fiquem desativados em caso de URL inválida
            return

        self.update_status("Carregando resoluções e thumbnail...", 'orange')
        self.update_download_button_state(False) # Desativa os botões durante o carregamento
        self.resolution_cb.set("Carregando...")
        self.resolution_cb['values'] = [] # Limpa valores anteriores
        self.thumbnail_label.config(image='', text="Carregando...")

        # Inicia uma nova thread para a operação que pode demorar
        threading.Thread(target=self._load_resolutions_task, args=(url,)).start()

    def _load_resolutions_task(self, url):
        """Tarefa a ser executada em uma thread separada para carregar resoluções."""
        cookies = self.cookie_path_var.get() or None
        resolutions, thumbnail, error_msg = get_resolutions(url, cookies)

        # Agenda atualizações da UI na thread principal
        self.after(0, self._update_resolutions_gui, resolutions, thumbnail, error_msg)

    def _update_resolutions_gui(self, resolutions, thumbnail, error_msg):
        """Atualiza a GUI com as resoluções e thumbnail carregadas."""
        if error_msg:
            messagebox.showerror("Erro ao Carregar", error_msg)
            self.update_status(f"Erro ao carregar: {error_msg}", 'red')
            self.resolution_cb['values'] = []
            self.resolution_cb.set("Nenhuma resolução encontrada.")
            self.thumbnail_label.config(image='', text="Preview da Thumbnail")
            self.thumbnail_image = None
            self.update_download_button_state(False) # Desativa os botões em caso de erro

        else:
            if resolutions:
                self.resolution_cb['values'] = resolutions
                self.resolution_cb.set(resolutions[0]) # Seleciona a primeira resolução
                self.update_status("Resoluções carregadas com sucesso! Agora você pode baixar.", 'green')
                self.update_download_button_state(True) # Ativa os botões de download
            else:
                self.resolution_cb['values'] = []
                self.resolution_cb.set("Nenhuma resolução encontrada.")
                self.update_status("Nenhuma resolução de vídeo encontrada para esta URL.", 'orange')
                self.update_download_button_state(False) # Mantém desativado se não houver resoluções

            if thumbnail:
                self.thumbnail_url = thumbnail
                self.after(0, self._load_thumbnail_image, thumbnail) # Carrega thumbnail em segundo plano
            else:
                self.thumbnail_url = None
                self.thumbnail_label.config(image='', text="Nenhuma Thumbnail disponível.")
                self.thumbnail_image = None

    def _load_thumbnail_image(self, thumbnail_url):
        """Carrega a imagem da thumbnail em uma thread separada."""
        try:
            response = requests.get(thumbnail_url, timeout=10) # Adiciona timeout
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image.thumbnail((150, 100), Image.Resampling.LANCZOS) # Redimensiona com LANCZOS para melhor qualidade
            self.thumbnail_image = ImageTk.PhotoImage(image)
            self.thumbnail_label.config(image=self.thumbnail_image, text="")
        except requests.exceptions.RequestException as e:
            self.thumbnail_label.config(image='', text=f"Erro de rede: {e}")
            self.thumbnail_image = None
        except Exception as e:
            self.thumbnail_label.config(image='', text=f"Erro ao carregar thumbnail: {e}")
            self.thumbnail_image = None
        finally:
            # Se houve um erro e nenhuma imagem de thumbnail foi definida, redefine o texto
            if not self.thumbnail_image:
                self.thumbnail_label.config(text="Preview da Thumbnail")

    def progress_hook(self, d):
        """Hook de progresso para yt-dlp."""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes and total_bytes > 0: # Garante que total_bytes não seja zero
                percent = (downloaded_bytes / total_bytes) * 100
                self.after(0, self.progress_var.set, percent) # Atualiza na thread principal
                # Atualiza o status com a velocidade de download e tempo restante, se disponível
                speed = d.get('speed')
                eta = d.get('eta')
                status_msg = f"Baixando: {percent:.1f}%"
                if speed:
                    status_msg += f" | Velocidade: {speed/1024:.2f} KiB/s"
                if eta is not None:
                    # Formata ETA para minutos e segundos se for um número grande
                    if isinstance(eta, (int, float)) and eta >= 60:
                        minutes = int(eta // 60)
                        seconds = int(eta % 60)
                        status_msg += f" | Tempo restante: {minutes}m {seconds}s"
                    else:
                        status_msg += f" | Tempo restante: {eta}s"
                self.after(0, self.update_status, status_msg, 'blue')
            else:
                self.after(0, self.update_status, "Baixando: Progresso desconhecido...", 'blue')
        elif d['status'] == 'finished':
            self.after(0, self.progress_var.set, 100)
            self.after(0, self.update_status, "Processando, aguarde...", 'green') # Processando após o download
        elif d['status'] == 'error':
            self.after(0, self.progress_var.set, 0)
            self.after(0, self.update_status, f"Erro no download: {d.get('error', 'Desconhecido')}", 'red')
            messagebox.showerror("Erro de Download", f"Ocorreu um erro durante o download: {d.get('error', 'Detalhes desconhecidos.')}")

    def download_video_threaded(self):
        """Inicia o download do vídeo em uma nova thread."""
        url = self.url_var.get()
        resolution = self.resolution_var.get()
        output_path = self.output_path_var.get()
        video_format = self.format_var.get()
        cookies = self.cookie_path_var.get() or None

        if not url:
            messagebox.showwarning("Entrada Ausente", "Por favor, insira a URL do vídeo.")
            return
        if not resolution or resolution == "Selecione...":
            messagebox.showwarning("Entrada Ausente", "Por favor, selecione uma resolução.")
            return
        if not output_path:
            messagebox.showwarning("Entrada Ausente", "Por favor, selecione um caminho de saída.")
            return

        self.update_status("Iniciando download do vídeo...", 'blue')
        self.progress_var.set(0)
        self.update_download_button_state(False) # Desativa os botões durante o download

        threading.Thread(target=self._download_video_task, 
                         args=(url, resolution, output_path, self.progress_hook, cookies, video_format)).start()

    def _download_video_task(self, url, resolution, output_path, progress_hook, cookies, video_format):
        """Tarefa de download de vídeo para execução em thread."""
        result = download_video(url, resolution, output_path, progress_hook, cookies, video_format)
        self.after(0, self._post_download_task_gui, result)

    def _post_download_task_gui(self, result_message):
        """Atualiza a GUI após a conclusão do download do vídeo."""
        if "finalizado com sucesso" in result_message:
            self.update_status(result_message, 'green')
            messagebox.showinfo("Download Concluído", result_message)
            self.progress_var.set(100) # Garante que chegue a 100 no sucesso
        else:
            self.update_status(result_message, 'red')
            messagebox.showerror("Erro de Download", result_message)
            self.progress_var.set(0) # Reseta o progresso no erro
        self.update_download_button_state(True) # Reativa os botões

    def download_thumbnail_threaded(self):
        """Inicia o download da thumbnail em uma nova thread."""
        if not self.thumbnail_url:
            messagebox.showwarning("Aviso", "Nenhuma thumbnail carregada para download.")
            return
            
        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showwarning("Entrada Ausente", "Por favor, selecione um caminho de saída para a thumbnail.")
            return

        self.update_status("Iniciando download da thumbnail...", 'blue')
        self.update_download_button_state(False)

        threading.Thread(target=self._download_thumbnail_task, 
                         args=(self.thumbnail_url, output_path)).start()

    def _download_thumbnail_task(self, thumbnail_url, output_path):
        """Tarefa de download de thumbnail para execução em thread."""
        result = download_thumbnail(thumbnail_url, output_path)
        self.after(0, self._post_thumbnail_task_gui, result)

    def _post_thumbnail_task_gui(self, result_message):
        """Atualiza a GUI após a conclusão do download da thumbnail."""
        if "Thumbnail salva em" in result_message:
            self.update_status(result_message, 'green')
            messagebox.showinfo("Download Concluído", result_message)
        else:
            self.update_status(result_message, 'red')
            messagebox.showerror("Erro de Download", result_message)
        self.update_download_button_state(True)

    def download_subtitle_threaded(self):
        """Inicia o download da legenda em uma nova thread."""
        url = self.url_var.get()
        output_path = self.output_path_var.get()

        if not url:
            messagebox.showwarning("Entrada Ausente", "Por favor, insira a URL do vídeo para baixar a legenda.")
            return
        if not output_path:
            messagebox.showwarning("Entrada Ausente", "Por favor, selecione um caminho de saída para a legenda.")
            return

        self.update_status("Iniciando download da legenda (idioma padrão: en)...", 'blue')
        self.update_download_button_state(False)

        threading.Thread(target=self._download_subtitle_task, 
                         args=(url, output_path, "en")).start() # Padrão para Inglês, pode ser uma configuração do usuário

    def _download_subtitle_task(self, url, output_path, language):
        """Tarefa de download de legenda para execução em thread."""
        result = download_subtitles(url, output_path, language)
        self.after(0, self._post_subtitle_task_gui, result)

    def _post_subtitle_task_gui(self, result_message):
        """Atualiza a GUI após a conclusão do download da legenda."""
        if "baixada com sucesso" in result_message:
            self.update_status(result_message, 'green')
            messagebox.showinfo("Legenda Concluída", result_message)
        else:
            self.update_status(result_message, 'red')
            messagebox.showerror("Erro na Legenda", result_message)
        self.update_download_button_state(True)

    def download_all_threaded(self):
        """Inicia o download completo (vídeo, thumbnail e legenda) em uma nova thread."""
        url = self.url_var.get()
        resolution = self.resolution_var.get()
        output_path = self.output_path_var.get()
        video_format = self.format_var.get()
        cookies = self.cookie_path_var.get() or None

        if not url:
            messagebox.showwarning("Entrada Ausente", "Por favor, insira a URL do vídeo.")
            return
        if not resolution or resolution == "Selecione...":
            messagebox.showwarning("Entrada Ausente", "Por favor, selecione uma resolução.")
            return
        if not output_path:
            messagebox.showwarning("Entrada Ausente", "Por favor, selecione um caminho de saída.")
            return

        self.update_status("Iniciando download completo...", 'blue')
        self.progress_var.set(0)
        self.update_download_button_state(False)

        threading.Thread(
            target=self._download_all_task,
            args=(url, resolution, output_path, self.progress_hook, cookies, video_format, self.thumbnail_url),
            daemon=True
        ).start()

    def _download_all_task(self, url, resolution, output_path, progress_hook, cookies, video_format, thumbnail_url):
        """Executa o download completo em thread."""
        # Baixa o vídeo
        video_result = download_video(url, resolution, output_path, progress_hook, cookies, video_format)
        # Baixa a thumbnail (se disponível)
        if thumbnail_url:
            thumb_result = download_thumbnail(thumbnail_url, output_path)
        else:
            thumb_result = "Nenhuma thumbnail disponível."
        # Baixa a legenda (padrão: en)
        subtitle_result = download_subtitles(url, output_path, "en")

        # Junta os resultados e atualiza a interface
        result_message = f"{video_result}\n{thumb_result}\n{subtitle_result}"
        self.after(0, self._post_download_all_task_gui, result_message)

    def _post_download_all_task_gui(self, result_message):
        """Atualiza a GUI após o download completo."""
        if "finalizado com sucesso" in result_message and "Nenhuma thumbnail disponível" not in result_message and "não disponível para este vídeo" not in result_message:
            self.update_status("Download completo finalizado!", 'green')
            messagebox.showinfo("Download Completo", result_message)
            self.progress_var.set(100)
        else:
            self.update_status("Algum item falhou no download ou não estava disponível.", 'red')
            messagebox.showerror("Erro no Download Completo", result_message)
            self.progress_var.set(0)
        self.update_download_button_state(True)

if __name__ == '__main__':
    app = DownloadiumApp()
    app.mainloop()
