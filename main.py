"""
Point d'entrée de l'application Pynote.
Lancer avec : python main.py
"""

from app.app import PynoteApp


def main() -> None:
    app = PynoteApp()
    app.mainloop()


if __name__ == "__main__":
    main()
