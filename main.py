"""
Point d'entrée de l'application Pynote.
Lancer avec : python main.py
"""

import sys
import os


def _set_appid() -> None:
    """Force Windows à utiliser l'icône de Pynote dans la barre des tâches."""
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
    from app.error_handler import install_global_handler
    from app.updater import check_for_updates

    app = PynoteApp()

    # Gestionnaire d'erreurs global
    install_global_handler(app)

    # Vérification silencieuse des mises à jour au démarrage (5s de délai)
    app.after(5000, lambda: check_for_updates(app, silent=True))

    app.mainloop()


if __name__ == "__main__":
    main()
