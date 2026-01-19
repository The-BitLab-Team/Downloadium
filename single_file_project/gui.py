from __future__ import annotations

import os
import queue
import re
import threading
from dataclasses import dataclass
from typing import Optional

from backend import DownloadManager, get_resolutions, validate_url


@dataclass
class ProgressState:
    current: Optional[int] = None
    total: Optional[int] = None
    status: str = "Pronto"
    percent: Optional[float] = None


_PROGRESS_RE = re.compile(
    r"(?:Video\s+(?P<cur>\d+)\s+of\s+(?P<tot>\d+)\s+\|\s+)?Status:\s+(?P<status>[^|]+?)(?:\s+\|\s+(?P<pct>\d+(?:\.\d+)?)%)?$"
)


def _parse_progress_line(line: str) -> ProgressState:
    line = (line or "").strip()
    m = _PROGRESS_RE.search(line)
    if not m:
        return ProgressState(status=line or "")

    cur = m.group("cur")
    tot = m.group("tot")
    status = (m.group("status") or "").strip()
    pct = m.group("pct")

    return ProgressState(
        current=int(cur) if cur else None,
        total=int(tot) if tot else None,
        status=status or (line or ""),
        percent=float(pct) if pct else None,
    )


class DownloadiumApp:
    """GUI principal.

    Preferencialmente usa customtkinter; se não estiver disponível, cai para ttk.
    """

    def __init__(self) -> None:
        try:
            import customtkinter as ctk  # type: ignore

            self._ctk = ctk
            self._use_ctk = True
        except Exception:
            self._ctk = None
            self._use_ctk = False

        if self._use_ctk:
            self._init_ctk()
        else:
            self._init_ttk_fallback()

    # -----------------
    # customtkinter UI
    # -----------------

    def _init_ctk(self) -> None:
        ctk = self._ctk
        assert ctk is not None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("Downloadium")
        self.root.minsize(860, 520)

        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker: Optional[threading.Thread] = None

        self.url_var = ctk.StringVar(value="")
        self.output_var = ctk.StringVar(value=os.path.join(os.getcwd(), "videos"))
        self.cookies_var = ctk.StringVar(value="")
        self.resolution_var = ctk.StringVar(value="Melhor")
        self.format_var = ctk.StringVar(value="mp4")

        self._progress_state = ProgressState()

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.root)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Downloadium", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=12
        )
        ctk.CTkLabel(
            header,
            text="Canal / Playlist / Vídeo — organiza em channel/playlist/title.ext",
            text_color=("#AAB4C3", "#AAB4C3"),
        ).grid(row=0, column=1, sticky="w", padx=8, pady=12)

        body = ctk.CTkFrame(self.root)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(2, weight=1)

        # Left: inputs
        inputs = ctk.CTkFrame(body)
        inputs.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=12)
        inputs.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(inputs, text="URL", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 6)
        )
        self.url_entry = ctk.CTkEntry(inputs, textvariable=self.url_var, placeholder_text="https://...")
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=12)

        row2 = ctk.CTkFrame(inputs, fg_color="transparent")
        row2.grid(row=2, column=0, sticky="ew", padx=12, pady=(10, 6))
        row2.grid_columnconfigure(0, weight=1)
        row2.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(row2, text="Pasta de saída", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(row2, text="Procurar", width=120, command=self._browse_output).grid(
            row=0, column=1, sticky="e"
        )

        self.output_entry = ctk.CTkEntry(inputs, textvariable=self.output_var)
        self.output_entry.grid(row=3, column=0, sticky="ew", padx=12)

        row4 = ctk.CTkFrame(inputs, fg_color="transparent")
        row4.grid(row=4, column=0, sticky="ew", padx=12, pady=(10, 6))
        row4.grid_columnconfigure(0, weight=1)
        row4.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(row4, text="Cookies (opcional)", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(row4, text="Selecionar", width=120, command=self._browse_cookies).grid(
            row=0, column=1, sticky="e"
        )

        self.cookies_entry = ctk.CTkEntry(inputs, textvariable=self.cookies_var, placeholder_text="cookies.txt")
        self.cookies_entry.grid(row=5, column=0, sticky="ew", padx=12)

        row6 = ctk.CTkFrame(inputs, fg_color="transparent")
        row6.grid(row=6, column=0, sticky="ew", padx=12, pady=(12, 6))
        row6.grid_columnconfigure(0, weight=1)
        row6.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row6, text="Resolução", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(row6, text="Formato", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")

        self.resolution_menu = ctk.CTkOptionMenu(
            row6,
            variable=self.resolution_var,
            values=["Melhor"],
            width=220,
        )
        self.resolution_menu.grid(row=1, column=0, sticky="ew", pady=(6, 0), padx=(0, 10))

        self.format_menu = ctk.CTkOptionMenu(
            row6,
            variable=self.format_var,
            values=["mp4", "mkv"],
            width=180,
        )
        self.format_menu.grid(row=1, column=1, sticky="ew", pady=(6, 0))

        actions = ctk.CTkFrame(inputs)
        actions.grid(row=7, column=0, sticky="ew", padx=12, pady=(14, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(actions, text="Carregar Resoluções", command=self._load_resolutions).grid(
            row=0, column=0, sticky="ew", padx=(0, 8), pady=10
        )
        ctk.CTkButton(actions, text="Iniciar Download", fg_color="#2563EB", command=self._start_download).grid(
            row=0, column=1, sticky="ew", padx=(8, 0), pady=10
        )

        # Right: progress + log
        panel = ctk.CTkFrame(body)
        panel.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(8, 12), pady=12)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        self.video_label = ctk.CTkLabel(panel, text="Video —", font=ctk.CTkFont(size=18, weight="bold"))
        self.video_label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 2))

        self.status_label = ctk.CTkLabel(panel, text="Status: Pronto", font=ctk.CTkFont(size=14))
        self.status_label.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(panel)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=12)
        self.progress_bar.set(0.0)

        self.percent_label = ctk.CTkLabel(panel, text="0%", text_color=("#AAB4C3", "#AAB4C3"))
        self.percent_label.grid(row=2, column=0, sticky="e", padx=12)

        ctk.CTkLabel(panel, text="Eventos", font=ctk.CTkFont(weight="bold")).grid(
            row=3, column=0, sticky="w", padx=12, pady=(12, 6)
        )
        self.log = ctk.CTkTextbox(panel, height=200)
        self.log.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self.root.after(100, self._poll_queue)

    def _browse_output(self) -> None:
        import tkinter.filedialog as fd

        path = fd.askdirectory(title="Selecione a pasta de saída")
        if path:
            self.output_var.set(path)

    def _browse_cookies(self) -> None:
        import tkinter.filedialog as fd

        path = fd.askopenfilename(title="Selecione o arquivo de cookies", filetypes=[("Text", "*.txt"), ("All", "*")])
        if path:
            self.cookies_var.set(path)

    def _append_log(self, line: str) -> None:
        try:
            self.log.insert("end", line.rstrip() + "\n")
            self.log.see("end")
        except Exception:
            pass

    def _set_progress_ui(self, state: ProgressState) -> None:
        # Video label
        if state.current is not None and state.total is not None:
            self.video_label.configure(text=f"Video {state.current}/{state.total}")
        elif state.total is not None:
            self.video_label.configure(text=f"Video —/{state.total}")
        else:
            self.video_label.configure(text="Video —")

        self.status_label.configure(text=f"Status: {state.status}")

        if state.percent is None:
            return

        if self._use_ctk:
            self.progress_bar.set(max(0.0, min(1.0, state.percent / 100.0)))
            self.percent_label.configure(text=f"{state.percent:.1f}%")
        else:
            self._progress_var.set(float(state.percent))

    def _load_resolutions(self) -> None:
        url = self.url_var.get().strip()
        cookies = self.cookies_var.get().strip() or None

        if not validate_url(url):
            self._append_log("URL inválida ou não suportada.")
            return

        self._append_log("Carregando resoluções...")

        def work() -> None:
            resolutions, _thumb, err = get_resolutions(url, cookies_file=cookies)
            if err:
                self._queue.put(("log", f"Erro: {err}"))
                return
            self._queue.put(("resolutions", resolutions))
            self._queue.put(("log", f"Resoluções: {', '.join(resolutions[:6])}{'...' if len(resolutions) > 6 else ''}"))

        threading.Thread(target=work, daemon=True).start()

    def _start_download(self) -> None:
        if self._worker and self._worker.is_alive():
            self._append_log("Download já em andamento.")
            return

        url = self.url_var.get().strip()
        if not validate_url(url):
            self._append_log("URL inválida ou não suportada.")
            return

        output_path = self.output_var.get().strip()
        if not output_path:
            self._append_log("Selecione uma pasta de saída.")
            return

        resolution = self.resolution_var.get().strip() or "Melhor"
        video_format = self.format_var.get().strip() or "mp4"
        cookies = self.cookies_var.get().strip() or None

        self._append_log("Iniciando download...")
        self._progress_state = ProgressState(status="Starting", percent=0.0)
        self._set_progress_ui(self._progress_state)

        def on_progress(line: str, percent: Optional[float]) -> None:
            # Normaliza percent vindo separado
            state = _parse_progress_line(line)
            if percent is not None:
                state.percent = percent
            self._queue.put(("progress", state))
            self._queue.put(("log", line))

        def work() -> None:
            manager = DownloadManager(
                output_path=output_path,
                resolution=resolution,
                video_format=video_format,
                cookies_file=cookies,
            )
            result = manager.download(url, on_progress)
            self._queue.put(("log", result))
            # força status final na UI
            self._queue.put(("done", result))

        self._worker = threading.Thread(target=work, daemon=True)
        self._worker.start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "progress":
                    state = payload  # type: ignore[assignment]
                    if isinstance(state, ProgressState):
                        # preserva valores anteriores quando vierem como None
                        if state.current is None:
                            state.current = self._progress_state.current
                        if state.total is None:
                            state.total = self._progress_state.total
                        if state.percent is None:
                            state.percent = self._progress_state.percent
                        if not state.status:
                            state.status = self._progress_state.status

                        self._progress_state = state
                        self._set_progress_ui(state)

                elif kind == "resolutions":
                    resolutions = payload  # type: ignore[assignment]
                    if isinstance(resolutions, list) and resolutions:
                        if self._use_ctk:
                            self.resolution_menu.configure(values=resolutions)
                        else:
                            self.resolution_combo["values"] = resolutions

                        if self.resolution_var.get() not in resolutions:
                            self.resolution_var.set(resolutions[0])

                elif kind == "log":
                    self._append_log(str(payload))

                elif kind == "done":
                    # Só melhora o texto, sem popup intrusivo
                    self._progress_state.status = "Done"
                    self._progress_state.percent = 100.0
                    self._set_progress_ui(self._progress_state)

        except queue.Empty:
            pass
        finally:
            self.root.after(120, self._poll_queue)

    def mainloop(self) -> None:
        self.root.mainloop()

    # -----------------
    # ttk fallback
    # -----------------

    def _init_ttk_fallback(self) -> None:
        import tkinter as tk
        from tkinter import filedialog, ttk

        self.root = tk.Tk()
        self.root.title("Downloadium")
        self.root.minsize(860, 520)

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker: Optional[threading.Thread] = None

        self.url_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value=os.path.join(os.getcwd(), "videos"))
        self.cookies_var = tk.StringVar(value="")
        self.resolution_var = tk.StringVar(value="Melhor")
        self.format_var = tk.StringVar(value="mp4")

        root = self.root
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        frm = ttk.Frame(root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="URL:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Saída:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Button(frm, text="Procurar", command=lambda: self.output_var.set(filedialog.askdirectory() or self.output_var.get())).grid(
            row=1, column=2, padx=(8, 0), pady=(8, 0)
        )

        ttk.Label(frm, text="Cookies (opcional):").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.cookies_var).grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Button(frm, text="Selecionar", command=self._browse_cookies).grid(
            row=2, column=2, padx=(8, 0), pady=(8, 0)
        )

        ttk.Label(frm, text="Resolução:").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.resolution_combo = ttk.Combobox(frm, textvariable=self.resolution_var, values=["Melhor"], state="readonly")
        self.resolution_combo.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="Formato:").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.format_combo = ttk.Combobox(frm, textvariable=self.format_var, values=["mp4", "mkv"], state="readonly")
        self.format_combo.grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Button(btns, text="Carregar Resoluções", command=self._load_resolutions).pack(side="left")
        ttk.Button(btns, text="Iniciar Download", command=self._start_download).pack(side="left", padx=(8, 0))

        prog = ttk.Frame(root, padding=12)
        prog.grid(row=1, column=0, sticky="nsew")
        prog.grid_columnconfigure(0, weight=1)

        self.video_label = ttk.Label(prog, text="Video —")
        self.video_label.grid(row=0, column=0, sticky="w")
        self.status_label = ttk.Label(prog, text="Status: Pronto")
        self.status_label.grid(row=1, column=0, sticky="w")

        self._progress_var = tk.DoubleVar(value=0.0)
        ttk.Progressbar(prog, variable=self._progress_var, maximum=100).grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.log = tk.Text(prog, height=10)
        self.log.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        prog.grid_rowconfigure(3, weight=1)

        self._progress_state = ProgressState()
        self.root.after(120, self._poll_queue)
