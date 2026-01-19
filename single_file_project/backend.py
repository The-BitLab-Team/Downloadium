from __future__ import annotations

import os
import re
import shutil
from typing import Any, Callable, Optional, cast
from urllib.parse import urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text or "")


def ensure_directory_exists(path: str) -> None:
    if path and not os.path.exists(path):
        os.makedirs(path)


def validate_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
        if not all([parsed.scheme, parsed.netloc]):
            return False

        supported_domains = [
            "youtube.com",
            "youtu.be",
            "vimeo.com",
            "dailymotion.com",
            "twitch.tv",
            "tiktok.com",
            "instagram.com",
            "facebook.com",
            "twitter.com",
            "x.com",
            "reddit.com",
            "soundcloud.com",
        ]

        domain = parsed.netloc.lower().replace("www.", "")
        return any(supported in domain for supported in supported_domains)
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[<>:\"/\\|?*]", "_", filename or "")


def get_resolutions(
    url: str,
    cookies_file: str | None = None,
) -> tuple[list[str], str | None, str | None]:
    if not validate_url(url):
        return [], None, "URL inválida ou não suportada."

    options: dict[str, Any] = {
        # Evita que configs globais do usuário (yt-dlp.conf) quebrem a listagem.
        # Ex.: um --format fixo pode disparar 'Requested format is not available'.
        "ignoreconfig": True,
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "nocolor": True,
        "cachedir": False,
        "retries": 5,
        "socket_timeout": 30,
        "extract_flat": False,
        "no_warnings": True,
        # Sobrescreve qualquer --format global para não falhar ao apenas listar formatos.
        "format": "bestvideo+bestaudio/best",
    }
    if cookies_file and os.path.exists(cookies_file):
        options["cookiefile"] = cookies_file

    try:
        with YoutubeDL(cast(Any, options)) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return [], None, "Não foi possível extrair informações do vídeo."

            formats = info.get("formats", [])
            if not formats:
                return [], None, "Nenhum formato disponível para este vídeo."

            resolutions_with_quality: list[tuple[int, str]] = []
            seen_resolutions: set[str] = set()

            for fmt in formats:
                format_note = fmt.get("format_note")
                vcodec = fmt.get("vcodec", "none")
                height = fmt.get("height")

                if vcodec != "none" and format_note and format_note not in seen_resolutions:
                    seen_resolutions.add(format_note)
                    try:
                        if height:
                            resolutions_with_quality.append((int(height), format_note))
                        else:
                            height_from_note = int("".join(filter(str.isdigit, format_note)))
                            resolutions_with_quality.append((height_from_note, format_note))
                    except Exception:
                        resolutions_with_quality.append((0, format_note))

            resolutions_with_quality.sort(key=lambda x: x[0], reverse=True)
            unique_resolutions = [r[1] for r in resolutions_with_quality]
            final_resolutions = ["Melhor"] + unique_resolutions if unique_resolutions else ["Melhor"]

            thumbnail = info.get("thumbnail")
            return final_resolutions, thumbnail, None

    except ExtractorError as e:
        return [], None, f"Erro ao extrair informações do vídeo: {_strip_ansi(str(e))}"
    except DownloadError as e:
        return [], None, f"Erro de download do yt-dlp: {_strip_ansi(str(e))}"
    except Exception as e:
        return [], None, f"Erro inesperado ao obter resoluções: {_strip_ansi(str(e))}"


def fetch_video_formats(url: str) -> list[dict[str, str]]:
    """Compat: usado por testes legados; lista formatos mp4/mkv por resolução."""
    if not validate_url(url):
        return []

    # Testes legados fazem patch em `youtube_downloader_gui.YoutubeDL`.
    # Importamos daqui para manter esse contrato.
    from youtube_downloader_gui import YoutubeDL as PatchedYoutubeDL

    with PatchedYoutubeDL({"skip_download": True, "quiet": True, "nocolor": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats", []) if info else []
    out: list[dict[str, str]] = []
    for fmt in formats:
        ext = (fmt.get("ext") or "").lower()
        if ext not in {"mp4", "mkv"}:
            continue
        format_note = fmt.get("format_note")
        format_id = fmt.get("format_id")
        if not (format_note and format_id):
            continue
        out.append({"format_id": str(format_id), "resolution": str(format_note), "ext": ext})

    def _height(res: str) -> int:
        digits = "".join(ch for ch in res if ch.isdigit())
        return int(digits) if digits.isdigit() else 0

    out.sort(key=lambda x: _height(x["resolution"]), reverse=True)
    return out


class DownloadManager:
    """Gerencia downloads via yt-dlp com suporte a canais/playlists, legendas embutidas e progresso avançado."""

    def __init__(
        self,
        output_path: str,
        resolution: str = "Melhor",
        video_format: str = "mp4",
        cookies_file: Optional[str] = None,
        sleep_interval: float = 2.0,
        max_sleep_interval: float = 5.0,
        sleep_interval_requests: float = 1.0,
    ):
        self.output_path = output_path
        self.resolution = resolution
        self.video_format = video_format
        self.cookies_file = cookies_file

        self.sleep_interval = sleep_interval
        self.max_sleep_interval = max_sleep_interval
        self.sleep_interval_requests = sleep_interval_requests

        self._total_videos: int = 0
        self._current_index: int = 0
        self._current_video_id: Optional[str] = None

    def _build_format_string(self) -> str:
        res = (self.resolution or "").strip().lower()
        if res == "melhor":
            return "bestvideo+bestaudio/best"

        digits = "".join(ch for ch in res if ch.isdigit())
        if digits.isdigit():
            height = int(digits)
            return f"bestvideo[height<={height}]+bestaudio/best"

        return "bestvideo+bestaudio/best"

    def fetch_metadata(self, url: str) -> int:
        """Conta quantos vídeos serão processados antes do download (UI: Video X/Y)."""
        if not url:
            raise ValueError("URL não fornecida")

        ydl_opts: dict[str, Any] = {
            "ignoreconfig": True,
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "noplaylist": False,
            "nocolor": True,
            "cachedir": False,
            "retries": 5,
            "socket_timeout": 30,
            "no_warnings": True,
            # Neutraliza configs globais com --format estrito.
            "format": "best",
        }
        if self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts["cookiefile"] = self.cookies_file

        with YoutubeDL(cast(Any, ydl_opts)) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            self._total_videos = 0
            return 0

        playlist_count = info.get("playlist_count")
        if isinstance(playlist_count, int) and playlist_count > 0:
            self._total_videos = playlist_count
            return playlist_count

        entries = info.get("entries")
        if entries is None:
            self._total_videos = 1
            return 1

        count = 0
        try:
            for _ in entries:
                count += 1
        except TypeError:
            count = 0

        self._total_videos = count if count > 0 else 1
        return self._total_videos

    def download(self, url: str, callback: Callable[[str, Optional[float]], None]) -> str:
        if not url:
            return "Erro: URL do vídeo não fornecida."
        if not self.output_path:
            return "Erro: Caminho de saída não fornecido."

        ensure_directory_exists(self.output_path)

        embed_enabled = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
        if not embed_enabled:
            try:
                callback(
                    "Aviso: ffmpeg/ffprobe não encontrado no PATH. Baixando sem embutir legendas.",
                    0.0,
                )
            except Exception:
                pass

        try:
            total = self.fetch_metadata(url)
        except Exception:
            total = 0

        self._current_index = 0
        self._current_video_id = None

        def emit(status: str, percent: Optional[float] = None) -> None:
            try:
                callback(status, percent)
            except Exception:
                pass

        if total > 0:
            emit(f"Video 0 of {total} | Status: Downloading", 0.0)
        else:
            emit("Status: Downloading", 0.0)

        def progress_hook(d: dict) -> None:
            status = d.get("status")
            info_dict = d.get("info_dict") or {}
            video_id = info_dict.get("id")

            if status == "downloading":
                if video_id and video_id != self._current_video_id:
                    self._current_video_id = video_id
                    self._current_index += 1

                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded_bytes = d.get("downloaded_bytes", 0)
                percent = None
                if isinstance(total_bytes, (int, float)) and total_bytes:
                    percent = max(0.0, min(100.0, (downloaded_bytes / total_bytes) * 100))

                if total > 0:
                    msg = f"Video {max(self._current_index, 1)} of {total} | Status: Downloading"
                else:
                    msg = "Status: Downloading"

                if percent is not None:
                    msg += f" | {percent:.1f}%"
                emit(msg, percent)

            elif status == "finished":
                if total > 0:
                    msg = f"Video {max(self._current_index, 1)} of {total} | Status: Encoding | 100.0%"
                else:
                    msg = "Status: Encoding | 100.0%"
                emit(msg, 100.0)

            elif status == "error":
                err = d.get("error")
                if total > 0:
                    msg = f"Video {max(self._current_index, 1)} of {total} | Status: Error"
                else:
                    msg = "Status: Error"
                if err:
                    msg += f" | {err}"
                emit(msg, 0.0)

        def postprocessor_hook(d: dict) -> None:
            pp = str(d.get("postprocessor") or "")
            pp_status = d.get("status")

            if total > 0:
                prefix = f"Video {max(self._current_index, 1)} of {total}"
            else:
                prefix = ""

            if "EmbedSubtitle" in pp:
                state = "Embedding Subtitles"
            else:
                state = "Encoding"

            if pp_status in {"started", "finished"}:
                msg = f"{prefix + ' | ' if prefix else ''}Status: {state}"
                emit(msg, None)

        outtmpl = os.path.join(
            self.output_path,
            "%(channel)s",
            "%(playlist)s",
            "%(title)s.%(ext)s",
        )

        ydl_opts: dict[str, Any] = {
            "ignoreconfig": True,
            "outtmpl": outtmpl,
            "outtmpl_na_placeholder": "Videos",
            "format": self._build_format_string(),
            "merge_output_format": self.video_format,
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [postprocessor_hook],
            "noplaylist": False,
            "nocolor": True,
            "windowsfilenames": True,
            "cachedir": False,
            "retries": 5,
            "fragment_retries": 5,
            "skip_unavailable_fragments": True,
            "keep_fragments": False,
            "no_warnings": True,
            "sleep_interval": self.sleep_interval,
            "max_sleep_interval": self.max_sleep_interval,
            "sleep_interval_requests": self.sleep_interval_requests,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en.*", "en"],
            "subtitlesformat": "best",
        }

        if embed_enabled:
            ydl_opts["embedsubtitles"] = True
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegEmbedSubtitle"},
            ]

        if self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts["cookiefile"] = self.cookies_file

        def run_once(opts: dict[str, Any]) -> None:
            with YoutubeDL(cast(Any, opts)) as ydl:
                ydl.download([url])

        try:
            run_once(ydl_opts)
            emit("Status: Done", 100.0)
            return "Download finalizado com sucesso!"
        except DownloadError as e:
            msg = str(e)
            lower = msg.lower()

            if "requested format is not available" in lower:
                try:
                    emit("Aviso: formato solicitado indisponível. Usando 'Melhor'...", None)
                    ydl_opts_retry = dict(ydl_opts)
                    ydl_opts_retry["format"] = "bestvideo+bestaudio/best"
                    run_once(ydl_opts_retry)
                    emit("Status: Done", 100.0)
                    return "Download finalizado com sucesso!"
                except Exception as e2:
                    return f"Erro no download (yt-dlp): {str(e2)}"

            if "rate-limited" in lower or "this content isn't available" in lower:
                return (
                    "YouTube aplicou rate-limit nesta sessão (pode durar até ~1h). "
                    "Tente novamente mais tarde; para reduzir recorrência, mantenha delays entre vídeos e, se possível, use cookies/login. "
                    f"Detalhe: {msg}"
                )

            return f"Erro no download (yt-dlp): {_strip_ansi(msg)}"
        except Exception as e:
            return f"Erro inesperado no download: {_strip_ansi(str(e))}"


def download_video(
    url: str,
    resolution: str,
    output_path: str,
    progress_hook: Optional[Callable[[str, Optional[float]], None]] = None,
    cookies_file: str | None = None,
    video_format: str = "mp4",
) -> str:
    manager = DownloadManager(
        output_path=output_path,
        resolution=resolution,
        video_format=video_format,
        cookies_file=cookies_file,
    )

    def _noop(_status: str, _percent: Optional[float] = None) -> None:
        return

    callback = progress_hook or _noop
    return manager.download(url, callback)
