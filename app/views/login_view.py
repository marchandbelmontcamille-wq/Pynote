"""
Vue de connexion — design refait.
"""

import logging
import threading
from typing import Callable

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.login")

C = {
    "bg":      "#0f1117",
    "card":    "#1c2333",
    "border":  "#2a3347",
    "accent":  "#4f8ef7",
    "text":    "#e8eaf0",
    "subtext": "#8892a4",
    "input":   "#151c2c",
    "danger":  "#e05252",
    "success": "#3dd68c",
}


class LoginView(ctk.CTkFrame):
    def __init__(self, master, service: PronoteService, on_success: Callable) -> None:
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self._service = service
        self._on_success = on_success
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_ui()
        if config.IS_DEV and config.PRONOTE_URL:
            self._entry_url.insert(0, config.PRONOTE_URL)
            self._entry_user.insert(0, config.PRONOTE_USER)
            self._entry_pass.insert(0, config.PRONOTE_PASS)

    def _build_ui(self) -> None:
        # Carte centrale
        card = ctk.CTkFrame(
            self,
            fg_color=C["card"],
            corner_radius=16,
            border_width=1,
            border_color=C["border"],
        )
        card.grid(row=0, column=0, padx=40, pady=40, ipadx=20, ipady=10)
        card.grid_columnconfigure(0, weight=1)

        # En-tête
        ctk.CTkLabel(
            card,
            text="🎓",
            font=ctk.CTkFont(size=48),
        ).grid(row=0, column=0, pady=(36, 4))

        ctk.CTkLabel(
            card,
            text="Pynote",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=C["text"],
        ).grid(row=1, column=0, pady=(0, 4))

        ctk.CTkLabel(
            card,
            text="Connectez-vous à votre espace Pronote",
            font=ctk.CTkFont(size=13),
            text_color=C["subtext"],
        ).grid(row=2, column=0, pady=(0, 28))

        # Champs
        self._entry_url = self._make_field(card, 3, "🔗  URL Pronote", "https://monlycee.index-education.net/pronote/eleve.html")
        self._entry_user = self._make_field(card, 5, "👤  Identifiant", "identifiant")
        self._entry_pass = self._make_field(card, 7, "🔒  Mot de passe", "••••••••", show="•")
        self._entry_pass.bind("<Return>", lambda _: self._on_connect())

        # Bouton connexion
        self._btn = ctk.CTkButton(
            card,
            text="Se connecter",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=48,
            width=380,
            corner_radius=10,
            fg_color=C["accent"],
            hover_color="#3a73d4",
            command=self._on_connect,
        )
        self._btn.grid(row=9, column=0, padx=40, pady=(20, 8))

        # Barre de progression
        self._progress = ctk.CTkProgressBar(
            card, width=380, mode="indeterminate",
            fg_color=C["border"], progress_color=C["accent"],
        )

        # Statut
        self._lbl_status = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=12),
            text_color=C["danger"], wraplength=360,
        )
        self._lbl_status.grid(row=11, column=0, padx=40, pady=(0, 32))

    def _make_field(self, parent, row: int, label: str, placeholder: str, show: str = "") -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["subtext"],
            anchor="w",
        ).grid(row=row, column=0, padx=40, sticky="w", pady=(0, 2))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=380,
            height=42,
            corner_radius=8,
            fg_color=C["input"],
            border_color=C["border"],
            border_width=1,
            text_color=C["text"],
            placeholder_text_color=C["subtext"],
            show=show,
            font=ctk.CTkFont(size=13),
        )
        entry.grid(row=row + 1, column=0, padx=40, pady=(0, 12))
        return entry

    def _on_connect(self) -> None:
        url = self._entry_url.get().strip()
        user = self._entry_user.get().strip()
        pwd = self._entry_pass.get()
        if not url or not user or not pwd:
            self._set_status("Veuillez remplir tous les champs.", error=True)
            return
        self._set_loading(True)
        threading.Thread(target=self._connect_thread, args=(url, user, pwd), daemon=True).start()

    def _connect_thread(self, url, user, pwd) -> None:
        try:
            self._service.connect(url, user, pwd)
            self.after(0, self._handle_success)
        except ConnectionError as exc:
            self.after(0, lambda: self._handle_error(str(exc)))

    def _handle_success(self) -> None:
        self._set_loading(False)
        self._on_success()

    def _handle_error(self, msg: str) -> None:
        self._set_loading(False)
        display = msg if config.IS_DEV else "Identifiants incorrects ou serveur inaccessible."
        self._set_status(display, error=True)

    def _set_loading(self, loading: bool) -> None:
        if loading:
            self._btn.configure(state="disabled", text="Connexion en cours…")
            self._progress.grid(row=10, column=0, padx=40, pady=(0, 8))
            self._progress.start()
        else:
            self._progress.stop()
            self._progress.grid_remove()
            self._btn.configure(state="normal", text="Se connecter")

    def _set_status(self, msg: str, *, error: bool = False) -> None:
        self._lbl_status.configure(
            text=msg,
            text_color=C["danger"] if error else C["success"],
        )
