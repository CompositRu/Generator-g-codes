from pathlib import Path
import sys, os, re

def get_desktop_path() -> Path:
    """
    Возвращает путь к рабочему столу текущего пользователя.
    Работает на Windows/macOS/Linux без знания имени пользователя.
    Если create=True — создаёт папку, если её нет (тихо игнорирует ошибки).
    """
    home = Path.home()

    if sys.platform.startswith("win"):
        # 1) Спросить у Windows «известную папку» Desktop
        try:
            # Простое решение:
            # os.path.join(r'C:\Users', os.getlogin(), 'Desktop')
            # Сложное решение:
            from ctypes import windll, wintypes, create_unicode_buffer
            CSIDL_DESKTOPDIRECTORY = 0x0010  # физическая папка Desktop (не виртуальная)
            SHGFP_TYPE_CURRENT = 0
            buf = create_unicode_buffer(wintypes.MAX_PATH)
            rv = windll.shell32.SHGetFolderPathW(
                None, CSIDL_DESKTOPDIRECTORY, None, SHGFP_TYPE_CURRENT, buf
            )
            if rv == 0:
                p = Path(buf.value)
            else:
                raise OSError(rv)
        except Exception:
            # 2) Фоллбэк: OneDrive Desktop → %USERPROFILE%\Desktop
            p = None
            for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
                od = os.environ.get(var)
                if od:
                    cand = Path(od) / "Desktop"
                    if cand.exists():
                        p = cand
                        break
            if p is None:
                p = Path(os.environ.get("USERPROFILE", str(home))) / "Desktop"

    elif sys.platform == "darwin":
        # macOS: стандартно ~/Desktop
        p = home / "Desktop"

    else:
        # Linux/*BSD: XDG сначала
        xdg = os.environ.get("XDG_DESKTOP_DIR")
        if xdg:
            p = Path(os.path.expandvars(xdg.replace("$HOME", str(home)))).expanduser()
        else:
            cfg = home / ".config" / "user-dirs.dirs"
            if cfg.exists():
                try:
                    txt = cfg.read_text(encoding="utf-8", errors="ignore")
                    m = re.search(r'XDG_DESKTOP_DIR=(?:"|\')(.+?)(?:"|\')', txt)
                    if m:
                        val = m.group(1).replace("$HOME", str(home))
                        p = Path(os.path.expandvars(val)).expanduser()
                    else:
                        p = home / "Desktop"
                except Exception:
                    p = home / "Desktop"
            else:
                p = home / "Desktop"

    return p
