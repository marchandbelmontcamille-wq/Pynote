"""
Gestionnaire d'erreurs global pour Pynote.
Capture les exceptions non gérées et affiche un dialog plutôt que de crasher silencieusement.
"""

import sys
import traceback
import logging
import customtkinter as ctk

logger = logging.getLogger("pynote.errors")

C = {
    "bg":     "#0f1117",
    "card":   "#1c2333",
    "border": "#2a3347",
    "text":   "#e8eaf0",
    "subtext":"#8892a4",
    "danger": "#e05252",
    "accent": "#4f8ef7",
}


class ErrorDialog(ctk.CTkToplevel):
    """Popup affichant un message d'erreur inattendue avec la stack trace."""

    def __init__(self, master, exc_type, exc_value, exc_tb):
        super().__init__(master)
        self.title("Erreur inattendue — Pynote")
        self.geometry("580x360")
        self.resizable(True, True)
        self.configure(fg_color=C["card"])
        self.grab_set()
        self.focus_force()

        # Centrer
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width()  - 580) // 2
        y = master.winfo_rooty() + (master.winfo_height() - 360) // 2
        self.geometry(f"+{max(0,x)}+{max(0,y)}")

        self._build(exc_type, exc_value, exc_tb)

    def _build(self, exc_type, exc_value, exc_tb) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Titre
        ctk.CTkLabel(
            self,
            text="⚠️  Une erreur inattendue s'est produite",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=C["danger"],
        ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            self,
            text=f"{exc_type.__name__}: {exc_value}",
            font=ctk.CTkFont(size=11),
            text_color=C["text"],
            wraplength=520,
            anchor="w",
        ).grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")

        # Stack trace scrollable
        tb_text = "".join(traceback.format_tb(exc_tb))
        box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#0a0d14",
            text_color=C["subtext"],
            border_width=1,
            border_color=C["border"],
            corner_radius=6,
        )
        box.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="nsew")
        box.insert("1.0", tb_text)
        box.configure(state="disabled")

        # Boutons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=24, pady=(0, 20), sticky="e")

        ctk.CTkButton(
            btn_frame,
            text="📋  Copier",
            width=100, height=32,
            font=ctk.CTkFont(size=11),
            fg_color=C["border"],
            hover_color="#3a4060",
            corner_radius=6,
            command=lambda: self._copy(f"{exc_type.__name__}: {exc_value}\n\n{tb_text}"),
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="Fermer",
            width=90, height=32,
            font=ctk.CTkFont(size=11),
            fg_color=C["accent"],
            hover_color="#3a6fd8",
            corner_radius=6,
            command=self.destroy,
        ).grid(row=0, column=1)

    def _copy(self, text: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass


def install_global_handler(root: ctk.CTk) -> None:
    """
    Installe un hook global d'exception pour afficher ErrorDialog
    au lieu de crasher silencieusement.
    Doit être appelé après la création de la fenêtre principale.
    """
    def _handler(exc_type, exc_value, exc_tb):
        logger.error("Exception non gérée", exc_info=(exc_type, exc_value, exc_tb))
        try:
            if root.winfo_exists():
                dlg = ErrorDialog(root, exc_type, exc_value, exc_tb)
                root.wait_window(dlg)
        except Exception:
            # Fallback si l'UI est déjà détruite
            traceback.print_exception(exc_type, exc_value, exc_tb)

    sys.excepthook = _handler
