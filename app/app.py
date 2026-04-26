"""
Fenêtre principale de l'application Pynote.
Gère la navigation entre la vue de connexion, l'EDT et les devoirs.
"""

import logging

import customtkinter as ctk

import config
from app.pronote_service import PronoteService
from app.views.login_view import LoginView
from app.views.edt_view import EdtView
from app.views.devoirs_view import DevoirsView

logger = logging.getLogger("pynote.app")

# Apparence globale
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NAV_ITEMS = [
    ("📅  Emploi du temps", "edt"),
    ("📝  Devoirs", "devoirs"),
]


class PynoteApp(ctk.CTk):
    """
    Fenêtre racine de l'application.
    Affiche d'abord LoginView, puis la navigation principale.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Pynote" + (" [DEV]" if config.IS_DEV else ""))
        self.geometry("900x620")
        self.minsize(720, 500)

        self._service = PronoteService()
        self._current_view: ctk.CTkFrame | None = None

        self._show_login()

    # ------------------------------------------------------------------
    # Phase 1 : Connexion
    # ------------------------------------------------------------------

    def _show_login(self) -> None:
        self._clear_window()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        login = LoginView(self, self._service, on_success=self._on_login_success)
        login.grid(row=0, column=0)
        logger.debug("LoginView affichée.")

    def _on_login_success(self) -> None:
        logger.info("Connexion validée — affichage de la vue principale.")
        self._show_main()

    # ------------------------------------------------------------------
    # Phase 2 : Interface principale
    # ------------------------------------------------------------------

    def _show_main(self) -> None:
        self._clear_window()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._sidebar = self._build_sidebar()
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        # Zone de contenu
        self._content_frame = ctk.CTkFrame(self)
        self._content_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_rowconfigure(0, weight=1)

        # Instancier les vues
        self._views: dict[str, ctk.CTkFrame] = {
            "edt": EdtView(self._content_frame, self._service),
            "devoirs": DevoirsView(self._content_frame, self._service),
        }
        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

        # Afficher la première vue
        self._switch_view("edt")

    def _build_sidebar(self) -> ctk.CTkFrame:
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(len(NAV_ITEMS) + 2, weight=1)

        # Logo / titre
        ctk.CTkLabel(
            sidebar,
            text="🎓 Pynote",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(24, 4))

        env_label = "DEV" if config.IS_DEV else "PROD"
        env_color = "#e67e22" if config.IS_DEV else "#2ecc71"
        ctk.CTkLabel(
            sidebar,
            text=env_label,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=env_color,
        ).grid(row=1, column=0, padx=20, pady=(0, 16))

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for i, (label, key) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                width=180,
                height=40,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=("gray75", "gray30"),
                command=lambda k=key: self._switch_view(k),
            )
            btn.grid(row=i + 2, column=0, padx=10, pady=4)
            self._nav_buttons[key] = btn

        # Bouton déconnexion en bas
        ctk.CTkButton(
            sidebar,
            text="⏏  Déconnexion",
            anchor="w",
            width=180,
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=("#c0392b", "#922b21"),
            text_color=("gray40", "gray70"),
            command=self._logout,
        ).grid(row=len(NAV_ITEMS) + 3, column=0, padx=10, pady=(0, 20), sticky="s")

        return sidebar

    def _switch_view(self, key: str) -> None:
        for k, btn in self._nav_buttons.items():
            btn.configure(
                fg_color=("gray75", "gray30") if k == key else "transparent"
            )
        self._views[key].tkraise()
        logger.debug("Vue active : %s", key)

    def _logout(self) -> None:
        self._service.disconnect()
        logger.info("Déconnexion — retour à la vue de connexion.")
        self._show_login()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _clear_window(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()
        # Réinitialiser la configuration de grille
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
