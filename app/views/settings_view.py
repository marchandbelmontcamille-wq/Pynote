"""
Vue Paramètres — réglages persistés dans %APPDATA%/Pynote/prefs.json.
"""

import json
import os
import logging
import customtkinter as ctk

import config

logger = logging.getLogger("pynote.settings")

C = {
    "bg":      "#0f1117",
    "card":    "#1c2333",
    "border":  "#2a3347",
    "accent":  "#4f8ef7",
    "text":    "#e8eaf0",
    "subtext": "#8892a4",
    "success": "#3dd68c",
    "warning": "#f5a623",
    "danger":  "#e05252",
}

_PREFS_FILE = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "Pynote", "prefs.json"
)


def _load_prefs() -> dict:
    try:
        with open(_PREFS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_prefs(prefs: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_PREFS_FILE), exist_ok=True)
        with open(_PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error("Impossible de sauvegarder les préférences : %s", exc)


class SettingsView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self._prefs = _load_prefs()
        self._build_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── En-tête ───────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="⚙️  Paramètres",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, padx=24, sticky="w")

        # ── Zone de défilement ────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"], corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        # ── Section : Notation ────────────────────────────────────────
        row = self._section(scroll, "📊  Notation", row)

        row = self._setting_row(
            scroll, row,
            label="Système de notation",
            desc="Trimestres (3 périodes) ou Semestres (2 périodes)",
            widget_fn=self._make_period_type_widget,
        )

        # ── Section : Affichage ───────────────────────────────────────
        row = self._section(scroll, "🎨  Affichage", row)

        row = self._setting_row(
            scroll, row,
            label="Thème de l'application",
            desc="Mode sombre uniquement pour l'instant",
            widget_fn=self._make_theme_widget,
        )

        # ── Section : À propos ────────────────────────────────────────
        row = self._section(scroll, "ℹ️  À propos", row)

        row = self._about_row(scroll, row)

    # ------------------------------------------------------------------
    # Widgets de paramètres
    # ------------------------------------------------------------------

    def _make_period_type_widget(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        current = self._prefs.get("period_type", "trimestre")

        var = ctk.StringVar(value="Trimestres" if current == "trimestre" else "Semestres")

        def on_change(val: str) -> None:
            self._prefs["period_type"] = "trimestre" if val == "Trimestres" else "semestre"
            _save_prefs(self._prefs)
            self._show_saved_toast()

        menu = ctk.CTkOptionMenu(
            frame,
            variable=var,
            values=["Trimestres", "Semestres"],
            width=160, height=32,
            font=ctk.CTkFont(size=11),
            fg_color=C["border"],
            button_color=C["accent"],
            button_hover_color="#3a6fd8",
            command=on_change,
        )
        menu.pack()
        return frame

    def _make_theme_widget(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(
            frame,
            text="🌙  Sombre",
            font=ctk.CTkFont(size=11),
            text_color=C["subtext"],
            fg_color=C["border"],
            corner_radius=6,
            width=100, height=28,
        ).pack()
        return frame

    # ------------------------------------------------------------------
    # Section "À propos"
    # ------------------------------------------------------------------

    def _about_row(self, parent, row: int) -> int:
        card = ctk.CTkFrame(
            parent, fg_color=C["card"], corner_radius=10,
            border_width=1, border_color=C["border"],
        )
        card.grid(row=row, column=0, sticky="ew", padx=24, pady=6)
        card.grid_columnconfigure(0, weight=1)

        import sys
        # En mode script non bundlé → toujours DEV
        _is_bundled = hasattr(sys, "_MEIPASS")
        if _is_bundled:
            _env = "DEV" if config.IS_DEV else "Stable"
        else:
            _env = "DEV (local)"

        items = [
            ("Version",      config.APP_VERSION),
            ("Environnement", _env),
            ("Licence",      "MIT — marchandbelmontcamille-wq"),
            ("GitHub",       "github.com/marchandbelmontcamille-wq/Pynote"),
            ("Basé sur",     "pronotepy + CustomTkinter"),
        ]
        for i, (k, v) in enumerate(items):
            ctk.CTkLabel(
                card, text=k,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=C["subtext"], anchor="w",
            ).grid(row=i, column=0, sticky="w", padx=20, pady=(10 if i == 0 else 2, 2 if i < len(items)-1 else 10))
            ctk.CTkLabel(
                card, text=v,
                font=ctk.CTkFont(size=11),
                text_color=C["text"], anchor="w",
            ).grid(row=i, column=1, sticky="w", padx=(4, 20), pady=(10 if i == 0 else 2, 2 if i < len(items)-1 else 10))

        return row + 1

    # ------------------------------------------------------------------
    # Toast "Sauvegardé"
    # ------------------------------------------------------------------

    def _show_saved_toast(self) -> None:
        toast = ctk.CTkLabel(
            self,
            text="✅  Paramètre sauvegardé",
            font=ctk.CTkFont(size=11),
            text_color="#0f1117",
            fg_color=C["success"],
            corner_radius=8,
            width=200, height=32,
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2000, toast.destroy)

    # ------------------------------------------------------------------
    # Helpers layout
    # ------------------------------------------------------------------

    def _section(self, parent, title: str, row: int) -> int:
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C["accent"], anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=24, pady=(20, 4))
        row += 1
        ctk.CTkFrame(parent, height=1, fg_color=C["border"]).grid(
            row=row, column=0, sticky="ew", padx=24, pady=(0, 8)
        )
        return row + 1

    def _setting_row(self, parent, row: int, label: str, desc: str, widget_fn) -> int:
        card = ctk.CTkFrame(
            parent, fg_color=C["card"], corner_radius=10,
            border_width=1, border_color=C["border"],
        )
        card.grid(row=row, column=0, sticky="ew", padx=24, pady=6)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["text"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(14, 2))

        ctk.CTkLabel(
            card, text=desc,
            font=ctk.CTkFont(size=10),
            text_color=C["subtext"], anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 14))

        widget = widget_fn(card)
        widget.grid(row=0, column=1, rowspan=2, padx=(8, 20), pady=10)

        return row + 1
