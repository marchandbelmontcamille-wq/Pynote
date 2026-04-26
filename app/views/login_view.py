"""
Vue de connexion à Pronote.
Affiche un formulaire URL / identifiant / mot de passe.
"""

import logging
import threading
from typing import Callable

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.login")


class LoginView(ctk.CTkFrame):
    """
    Panneau de connexion.

    :param master: Widget parent
    :param service: Instance partagée de PronoteService
    :param on_success: Callback appelé après connexion réussie
    """

    def __init__(
        self,
        master: ctk.CTk,
        service: PronoteService,
        on_success: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._service = service
        self._on_success = on_success
        self._build_ui()

        # Pré-remplir si mode dev et credentials dans .env
        if config.IS_DEV and config.PRONOTE_URL:
            self._entry_url.insert(0, config.PRONOTE_URL)
            self._entry_user.insert(0, config.PRONOTE_USER)
            self._entry_pass.insert(0, config.PRONOTE_PASS)
            logger.debug("Credentials pré-remplis depuis .env (mode DEV)")

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # Titre
        ctk.CTkLabel(
            self,
            text="🎓 Pynote",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, padx=40, pady=(40, 4))

        ctk.CTkLabel(
            self,
            text="Connexion à votre espace Pronote",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).grid(row=1, column=0, padx=40, pady=(0, 24))

        # URL
        ctk.CTkLabel(self, text="URL Pronote (page élève)").grid(
            row=2, column=0, padx=40, sticky="w"
        )
        self._entry_url = ctk.CTkEntry(
            self,
            placeholder_text="https://monlycee.index-education.net/pronote/eleve.html",
            width=380,
        )
        self._entry_url.grid(row=3, column=0, padx=40, pady=(2, 12))

        # Identifiant
        ctk.CTkLabel(self, text="Identifiant").grid(row=4, column=0, padx=40, sticky="w")
        self._entry_user = ctk.CTkEntry(self, placeholder_text="identifiant", width=380)
        self._entry_user.grid(row=5, column=0, padx=40, pady=(2, 12))

        # Mot de passe
        ctk.CTkLabel(self, text="Mot de passe").grid(row=6, column=0, padx=40, sticky="w")
        self._entry_pass = ctk.CTkEntry(
            self, placeholder_text="••••••••", show="•", width=380
        )
        self._entry_pass.grid(row=7, column=0, padx=40, pady=(2, 20))
        self._entry_pass.bind("<Return>", lambda _: self._on_connect())

        # Bouton connexion
        self._btn_connect = ctk.CTkButton(
            self,
            text="Se connecter",
            command=self._on_connect,
            width=380,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._btn_connect.grid(row=8, column=0, padx=40, pady=(0, 12))

        # Label statut / erreur
        self._lbl_status = ctk.CTkLabel(self, text="", text_color="red", wraplength=360)
        self._lbl_status.grid(row=9, column=0, padx=40, pady=(0, 40))

        # Indicateur de chargement
        self._progress = ctk.CTkProgressBar(self, width=380, mode="indeterminate")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_connect(self) -> None:
        url = self._entry_url.get().strip()
        user = self._entry_user.get().strip()
        pwd = self._entry_pass.get()

        if not url or not user or not pwd:
            self._set_status("Veuillez remplir tous les champs.", error=True)
            return

        self._set_loading(True)

        # Connexion dans un thread pour ne pas bloquer l'interface
        threading.Thread(
            target=self._connect_thread,
            args=(url, user, pwd),
            daemon=True,
        ).start()

    def _connect_thread(self, url: str, user: str, pwd: str) -> None:
        try:
            self._service.connect(url, user, pwd)
            self.after(0, self._handle_success)
        except ConnectionError as exc:
            self.after(0, lambda: self._handle_error(str(exc)))

    def _handle_success(self) -> None:
        self._set_loading(False)
        self._set_status("", error=False)
        self._on_success()

    def _handle_error(self, message: str) -> None:
        self._set_loading(False)
        display = message if config.IS_DEV else "Connexion impossible. Vérifiez vos identifiants."
        self._set_status(display, error=True)

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    def _set_loading(self, loading: bool) -> None:
        if loading:
            self._btn_connect.configure(state="disabled", text="Connexion en cours…")
            self._progress.grid(row=10, column=0, padx=40, pady=(0, 12))
            self._progress.start()
        else:
            self._progress.stop()
            self._progress.grid_remove()
            self._btn_connect.configure(state="normal", text="Se connecter")

    def _set_status(self, message: str, *, error: bool = False) -> None:
        color = "red" if error else "green"
        self._lbl_status.configure(text=message, text_color=color)
