from __future__ import annotations

import os
import shutil
from typing import Any, Callable, Optional, cast

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from Downloadium.backend.utils import ensure_directory_exists


class DownloadManager:
    """Gerencia downloads via yt-dlp com suporte a canais/playlists, legendas embutidas e progresso avançado."""

    def __init__(
        self,
        output_path: str = "videos",
        quality: str = "best",
        video_format: str = "mp4",
        cookies_file: Optional[str] = None,
    ):
        self.output_path = output_path
        self.quality = quality
        self.video_format = video_format
        self.cookies_file = cookies_file

        self._total_videos: int = 0
        self._current_index: int = 0
        self._current_video_id: Optional[str] = None

    def _build_format_string(self) -> str:
        q = (self.quality or "best").strip().lower()
        if q.endswith("p") and q[:-1].isdigit():
            height = int(q[:-1])
            return f"bestvideo[height<={height}]+bestaudio/best"
        if q in {"best", "worst"}:
            return q
        return self.quality

    def fetch_metadata(self, url: str) -> int:
        """Obtém metadados usando extract_flat=True para contar quantos vídeos serão processados."""
        if not url:
            raise ValueError("URL não fornecida")

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "noplaylist": False,
            "nocolor": True,
            "cachedir": False,
            "retries": 5,
            "socket_timeout": 30,
            "no_warnings": True,
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
        """Baixa vídeo/canal/playlist e emite updates via callback(status, percent)."""

        if not url:
            return "Erro: URL do vídeo não fornecida."

        ensure_directory_exists(self.output_path)

        embed_enabled = shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None
        if not embed_enabled:
            try:
                callback("Aviso: ffmpeg/ffprobe não encontrado no PATH. Baixando sem embutir legendas.", 0.0)
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
            # Legendas
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

        try:
            with YoutubeDL(cast(Any, ydl_opts)) as ydl:
                ydl.download([url])
            emit("Status: Done", 100.0)
            return f"Video downloaded successfully to {self.output_path}"
        except DownloadError as e:
            return f"Error downloading video (yt-dlp): {str(e)}"
        except Exception as e:
            return f"Error downloading video: {str(e)}"
