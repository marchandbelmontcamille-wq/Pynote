"""
Vue Devoirs — design refait.
"""

import logging
import threading
from datetime import date

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.devoirs")

C = {
    "bg":       "#0f1117",
    "card":     "#1c2333",
    "card2":    "#202840",
    "border":   "#2a3347",
    "accent":   "#4f8ef7",
    "text":     "#e8eaf0",
    "subtext":  "#8892a4",
    "success":  "#3dd68c",
    "warning":  "#f5a623",
    "danger":   "#e05252",
    "done":     "#2a3347",
    "day_head": "#161b27",
}

SUBJECT_COLORS = [
    "#4f8ef7", "#7c5cbf", "#3dd68c", "#f5a623",
    "#e05252", "#00bcd4", "#ff7043", "#ab47bc",
]


def _subject_color(name: str) -> str:
    return SUBJECT_COLORS[hash(name) % len(SUBJECT_COLORS)]


class DevoirsView(ctk.CTkFrame):
    def __init__(self, master, service: PronoteService) -> None:
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self._service = service
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # ── Barre supérieure ──
        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.grid(row=0, column=0, padx=24, pady=(20, 12), sticky="ew")
        topbar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topbar,
            text="Devoirs à venir",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            topbar,
            text="↻  Actualiser",
            width=110,
            height=36,
            corner_radius=8,
            fg_color=C["card"],
            hover_color=C["card2"],
            border_width=1,
            border_color=C["border"],
            font=ctk.CTkFont(size=12),
            text_color=C["text"],
            command=self.refresh,
        ).grid(row=0, column=1)

        # ── Zone défilante ──
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"],
        )
        self._scroll.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._lbl_info = ctk.CTkLabel(
            self._scroll, text="Chargement…",
            font=ctk.CTkFont(size=14), text_color=C["subtext"],
        )
        self._lbl_info.grid(row=0, column=0, pady=40)

    def refresh(self) -> None:
        self._clear_cards()
        self._lbl_info.configure(text="Chargement…", text_color=C["subtext"])
        self._lbl_info.grid(row=0, column=0, pady=40)
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            hw_list = self._service.get_homework()
            self.after(0, lambda: self._display_homework(hw_list))
        except Exception as exc:
            msg = str(exc) if config.IS_DEV else "Impossible de charger les devoirs."
            self.after(0, lambda: self._show_info(f"⚠  {msg}", error=True))

    def _display_homework(self, hw_list: list) -> None:
        self._lbl_info.grid_remove()
        self._clear_cards()

        if not hw_list:
            self._show_info("🎉  Aucun devoir à venir !", error=False)
            return

        today = date.today()
        days: dict[date, list] = {}
        for hw in hw_list:
            hw_date = hw.date if isinstance(hw.date, date) else hw.date.date()
            days.setdefault(hw_date, []).append(hw)

        row = 0
        for hw_date in sorted(days.keys()):
            delta = (hw_date - today).days

            if delta == 0:
                label = "Aujourd'hui"
                head_color = C["danger"]
            elif delta == 1:
                label = "Demain"
                head_color = C["warning"]
            elif delta <= 3:
                label = hw_date.strftime("%A %d %B").capitalize()
                head_color = C["warning"]
            else:
                label = hw_date.strftime("%A %d %B").capitalize()
                head_color = C["day_head"]

            # En-tête de date
            day_frame = ctk.CTkFrame(
                self._scroll,
                fg_color=head_color,
                corner_radius=7,
            )
            day_frame.grid(row=row, column=0, sticky="ew", pady=(10, 2))
            ctk.CTkLabel(
                day_frame,
                text=f"  📅  {label}  ·  {hw_date.strftime('%d/%m/%Y')}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff",
                anchor="w",
            ).grid(row=0, column=0, padx=10, pady=4, sticky="w")
            row += 1

            for hw in days[hw_date]:
                card = self._make_hw_card(hw)
                card.grid(row=row, column=0, sticky="ew", pady=1)
                row += 1

    def _make_hw_card(self, hw) -> ctk.CTkFrame:
        done = getattr(hw, "done", False)
        subject = getattr(hw, "subject", None)
        name = subject.name if subject else "Matière inconnue"
        color = C["done"] if done else _subject_color(name)

        icon = "✅" if done else "📝"
        desc = getattr(hw, "description", "") or ""
        desc = desc.replace("<br />", " ").replace("<br>", " ").strip()

        frame = ctk.CTkFrame(self._scroll, fg_color=C["card"], corner_radius=6)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(frame, width=3, fg_color=color, corner_radius=2).grid(
            row=0, column=0, rowspan=2, padx=(3, 6), pady=2, sticky="ns"
        )
        ctk.CTkLabel(frame, text=f"{icon}  {name}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["subtext"] if done else C["text"],
                     anchor="w").grid(row=0, column=1, pady=(2, 0), sticky="w")
        if desc:
            ctk.CTkLabel(frame, text=desc[:120] + ("…" if len(desc) > 120 else ""),
                         font=ctk.CTkFont(size=10),
                         text_color=C["subtext"], anchor="w",
                         wraplength=500, justify="left").grid(
                row=1, column=1, pady=(0, 2), sticky="w")
        return frame

    def _clear_cards(self) -> None:
        for w in self._scroll.winfo_children():
            if w is not self._lbl_info:
                w.destroy()

    def _show_info(self, msg: str, *, error: bool = False) -> None:
        self._lbl_info.configure(
            text=msg,
            text_color=C["danger"] if error else C["subtext"],
        )
        self._lbl_info.grid(row=0, column=0, pady=40)
