"""
Fenêtre principale de l'application Pynote — design refait.
"""

import logging
import sys
import os
import customtkinter as ctk

import config
from app.pronote_service import PronoteService
from app.views.login_view import LoginView
from app.views.edt_view import EdtView
from app.views.devoirs_view import DevoirsView

logger = logging.getLogger("pynote.app")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Palette de couleurs
C = {
    "bg":        "#0f1117",
    "sidebar":   "#161b27",
    "card":      "#1c2333",
    "border":    "#2a3347",
    "accent":    "#4f8ef7",
    "accent2":   "#7c5cbf",
    "text":      "#e8eaf0",
    "subtext":   "#8892a4",
    "success":   "#3dd68c",
    "warning":   "#f5a623",
    "danger":    "#e05252",
    "nav_hover": "#1e2740",
    "nav_active":"#1e2f55",
}

NAV_ITEMS = [
    ("edt",     "📅",  "Emploi du temps"),
    ("devoirs", "📝",  "Devoirs"),
]


class PynoteApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Pynote" + (" — DEV" if config.IS_DEV else ""))
        self.geometry("1050x680")
        self.minsize(800, 540)
        self.configure(fg_color=C["bg"])

        # Icône de la fenêtre (barre de titre + barre des tâches)
        _ico = self._find_icon()
        if _ico:
            try:
                self.iconbitmap(_ico)
            except Exception:
                pass

        self._service = PronoteService()
        self._show_login()

    @staticmethod
    def _find_icon() -> str | None:
        """Cherche assets/icon.ico — fonctionne en dev et dans le bundle PyInstaller."""
        # Bundle PyInstaller (sys._MEIPASS) ou dossier courant
        bases = []
        if hasattr(sys, "_MEIPASS"):
            bases.append(sys._MEIPASS)
        bases.append(os.path.dirname(os.path.abspath(__file__)))
        bases.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for base in bases:
            p = os.path.join(base, "assets", "icon.ico")
            if os.path.exists(p):
                return p
        return None

    # ------------------------------------------------------------------
    # Connexion
    # ------------------------------------------------------------------

    def _show_login(self) -> None:
        self._clear_window()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        LoginView(self, self._service, on_success=self._on_login_success).grid(
            row=0, column=0, sticky="nsew"
        )

    def _on_login_success(self) -> None:
        self._show_main()

    # ------------------------------------------------------------------
    # Interface principale
    # ------------------------------------------------------------------

    def _show_main(self) -> None:
        self._clear_window()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._build_sidebar().grid(row=0, column=0, sticky="nsew")

        # Zone de contenu
        content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        edt_view     = EdtView(content, self._service)
        devoirs_view = DevoirsView(content, self._service)

        self._views: dict[str, ctk.CTkFrame] = {
            "edt":     edt_view,
            "devoirs": devoirs_view,
        }
        for v in self._views.values():
            v.grid(row=0, column=0, sticky="nsew")

        self._switch_view("edt")
        # Charger les devoirs après un court délai pour ne pas surcharger
        self.after(2000, devoirs_view.refresh)

    def _build_sidebar(self) -> ctk.CTkFrame:
        sb = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=C["sidebar"])
        sb.grid_propagate(False)
        sb.grid_rowconfigure(10, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(sb, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(28, 24), sticky="w")

        ctk.CTkLabel(
            logo_frame,
            text="🎓",
            font=ctk.CTkFont(size=28),
        ).grid(row=0, column=0, padx=(0, 8))

        title_col = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_col.grid(row=0, column=1)
        ctk.CTkLabel(
            title_col,
            text="Pynote",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, sticky="w")
        version_label = f"DEV {config.APP_VERSION}" if config.IS_DEV else f"v{config.APP_VERSION}"
        ctk.CTkLabel(
            title_col,
            text=version_label,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=C["warning"] if config.IS_DEV else C["success"],
        ).grid(row=1, column=0, sticky="w")

        # Séparateur
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 12)
        )

        # Navigation
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for i, (key, icon, label) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                sb,
                text=f" {icon}  {label}",
                anchor="w",
                width=192,
                height=34,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                hover_color=C["nav_hover"],
                text_color=C["subtext"],
                corner_radius=6,
                border_spacing=0,
                command=lambda k=key: self._switch_view(k),
            )
            btn.grid(row=i + 2, column=0, padx=14, pady=2)
            self._nav_buttons[key] = btn

        # Séparateur bas
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).grid(
            row=10, column=0, sticky="ew", padx=16, pady=8
        )

        # Bouton déconnexion
        ctk.CTkButton(
            sb,
            text="  ⏏   Déconnexion",
            anchor="w",
            width=200,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#2a1a1a",
            text_color=C["subtext"],
            corner_radius=8,
            command=self._logout,
        ).grid(row=11, column=0, padx=10, pady=(0, 20))

        return sb

    def _switch_view(self, key: str) -> None:
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=C["nav_active"], text_color=C["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=C["subtext"])
        self._views[key].tkraise()

    def _logout(self) -> None:
        self._service.disconnect()
        self._show_login()

    def _clear_window(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        for i in range(3):
            self.grid_columnconfigure(i, weight=0)
