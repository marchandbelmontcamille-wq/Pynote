"""
Vue Devoirs.
Affiche les devoirs à rendre dans les 14 prochains jours.
"""

import logging
import threading
from datetime import date, timedelta

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.devoirs")


class DevoirsView(ctk.CTkFrame):
    """
    Affiche la liste des devoirs à venir.

    :param master: Widget parent
    :param service: Instance partagée de PronoteService
    """

    def __init__(self, master: ctk.CTk, service: PronoteService) -> None:
        super().__init__(master)
        self._service = service
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Barre d'outils
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            toolbar,
            text="Devoirs à venir",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            toolbar,
            text="↻ Actualiser",
            width=110,
            command=self.refresh,
        ).grid(row=0, column=1)

        # Zone défilante
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._lbl_info = ctk.CTkLabel(self._scroll, text="Chargement…", text_color="gray")
        self._lbl_info.grid(row=0, column=0, pady=20)

    # ------------------------------------------------------------------
    # Chargement des données
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Recharge les devoirs."""
        self._clear_cards()
        self._lbl_info.configure(text="Chargement…", text_color="gray")
        self._lbl_info.grid(row=0, column=0, pady=20)
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            homework_list = self._service.get_homework()
            self.after(0, lambda: self._display_homework(homework_list))
        except Exception as exc:
            msg = str(exc) if config.IS_DEV else "Erreur lors du chargement des devoirs."
            self.after(0, lambda: self._show_error(msg))

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------

    def _display_homework(self, homework_list: list) -> None:
        self._lbl_info.grid_remove()
        self._clear_cards()

        if not homework_list:
            self._lbl_info.configure(text="🎉 Aucun devoir à venir !", text_color="gray")
            self._lbl_info.grid(row=0, column=0, pady=20)
            return

        # Grouper par date d'échéance
        today = date.today()
        days: dict[date, list] = {}
        for hw in homework_list:
            hw_date = hw.date if isinstance(hw.date, date) else hw.date.date()
            days.setdefault(hw_date, []).append(hw)

        row = 0
        for hw_date in sorted(days.keys()):
            delta = (hw_date - today).days
            if delta == 0:
                label_date = "Aujourd'hui"
                color_header = ("orange", "#e67e22")
            elif delta == 1:
                label_date = "Demain"
                color_header = ("orange", "#e67e22")
            else:
                label_date = hw_date.strftime("%A %d %B").capitalize()
                color_header = ("gray85", "gray25")

            # En-tête de date
            header = ctk.CTkLabel(
                self._scroll,
                text=f"  📅 {label_date}  ({hw_date.strftime('%d/%m/%Y')})",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
                fg_color=color_header,
                corner_radius=6,
            )
            header.grid(row=row, column=0, padx=4, pady=(12, 4), sticky="ew")
            row += 1

            for hw in days[hw_date]:
                card = self._make_homework_card(hw)
                card.grid(row=row, column=0, padx=4, pady=2, sticky="ew")
                row += 1

    def _make_homework_card(self, hw) -> ctk.CTkFrame:
        """Crée une carte pour un devoir."""
        done = getattr(hw, "done", False)
        color = "#95a5a6" if done else "#3498db"

        frame = ctk.CTkFrame(self._scroll, corner_radius=8, border_width=2, border_color=color)
        frame.grid_columnconfigure(1, weight=1)

        # Bande colorée gauche
        ctk.CTkFrame(frame, width=6, fg_color=color, corner_radius=6).grid(
            row=0, column=0, rowspan=2, padx=(4, 8), pady=4, sticky="ns"
        )

        subject = getattr(hw, "subject", None)
        subject_name = subject.name if subject else "Matière inconnue"
        description = getattr(hw, "description", "") or ""

        # Nettoyer le HTML basique
        description = description.replace("<br />", "\n").replace("<br>", "\n")

        status_icon = "✅" if done else "📝"

        ctk.CTkLabel(
            frame,
            text=f"{status_icon}  {subject_name}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, padx=4, pady=(6, 2), sticky="w")

        if description:
            ctk.CTkLabel(
                frame,
                text=description[:200] + ("…" if len(description) > 200 else ""),
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                wraplength=480,
                justify="left",
            ).grid(row=1, column=1, padx=4, pady=(0, 6), sticky="w")

        return frame

    def _clear_cards(self) -> None:
        for widget in self._scroll.winfo_children():
            if widget is not self._lbl_info:
                widget.destroy()

    def _show_error(self, message: str) -> None:
        self._lbl_info.configure(text=f"⚠ {message}", text_color="red")
        self._lbl_info.grid(row=0, column=0, pady=20)
