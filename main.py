"""
Point d'entrée de l'application Pynote.
Lancer avec : python main.py
"""

import sys
import os


def _set_appid() -> None:
    """Force Windows à utiliser l'icône de Pynote dans la barre des tâches.

    Sans cet appel, la taskbar affiche l'icône de python.exe (ou du launcher).
    Le SetCurrentProcessExplicitAppUserModelID doit être appelé AVANT la
    création de toute fenêtre Tk/CTk.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "marchandbelmontcamille-wq.Pynote"
        )
    except Exception:
        pass


def main() -> None:
    _set_appid()
    from app.app import PynoteApp
    app = PynoteApp()
    app.mainloop()


if __name__ == "__main__":
    main()
