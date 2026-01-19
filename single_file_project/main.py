from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    # Garante imports locais quando executado a partir da raiz do repo
    this_dir = Path(__file__).resolve().parent
    if str(this_dir) not in sys.path:
        sys.path.insert(0, str(this_dir))

    from gui import DownloadiumApp

    app = DownloadiumApp()
    app.mainloop()


if __name__ == "__main__":
    main()
