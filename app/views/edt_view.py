"""
Vue Emploi du Temps.
Affiche les cours de la semaine sélectionnée.
"""

import logging
import threading
from datetime import date, timedelta

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.edt")

# Mapping abréviation jour → nom complet
JOURS = {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}

# Couleur par statut de cours
COULEUR_STATUT = {
    "Annulé": "#e74c3c",
    "Absent": "#e67e22",
    "": "#2ecc71",
}


class EdtView(ctk.CTkFrame):
    """
    Affiche l'emploi du temps hebdomadaire.

    :param master: Widget parent
    :param service: Instance partagée de PronoteService
    """

    def __init__(self, master: ctk.CTk, service: PronoteService) -> None:
        super().__init__(master)
        self._service = service
        self._current_monday = self._get_monday(date.today())
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Barre de navigation semaine
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        nav_frame.grid_columnconfigure(1, weight=1)

        self._btn_prev = ctk.CTkButton(
            nav_frame, text="◀ Sem. préc.", width=120, command=self._prev_week
        )
        self._btn_prev.grid(row=0, column=0, padx=(0, 8))

        self._lbl_semaine = ctk.CTkLabel(
            nav_frame,
            text="",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self._lbl_semaine.grid(row=0, column=1)

        self._btn_next = ctk.CTkButton(
            nav_frame, text="Sem. suiv. ▶", width=120, command=self._next_week
        )
        self._btn_next.grid(row=0, column=2, padx=(8, 0))

        # Zone défilante des cours
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        # Label chargement / erreur
        self._lbl_info = ctk.CTkLabel(self._scroll, text="Chargement…", text_color="gray")
        self._lbl_info.grid(row=0, column=0, pady=20)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _prev_week(self) -> None:
        self._current_monday -= timedelta(weeks=1)
        self.refresh()

    def _next_week(self) -> None:
        self._current_monday += timedelta(weeks=1)
        self.refresh()

    # ------------------------------------------------------------------
    # Chargement des données
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Recharge l'emploi du temps pour la semaine courante."""
        sunday = self._current_monday + timedelta(days=6)
        self._lbl_semaine.configure(
            text=f"Semaine du {self._current_monday.strftime('%d/%m/%Y')} au {sunday.strftime('%d/%m/%Y')}"
        )
        self._clear_lessons()
        self._lbl_info.configure(text="Chargement…", text_color="gray")
        self._lbl_info.grid(row=0, column=0, pady=20)

        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            lessons = self._service.get_timetable(self._current_monday)
            self.after(0, lambda: self._display_lessons(lessons))
        except Exception as exc:
            msg = str(exc) if config.IS_DEV else "Erreur lors du chargement de l'emploi du temps."
            self.after(0, lambda: self._show_error(msg))

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------

    def _display_lessons(self, lessons: list) -> None:
        self._lbl_info.grid_remove()
        self._clear_lessons()

        if not lessons:
            self._lbl_info.configure(text="Aucun cours cette semaine.", text_color="gray")
            self._lbl_info.grid(row=0, column=0, pady=20)
            return

        # Grouper par jour
        days: dict[int, list] = {}
        for lesson in lessons:
            weekday = lesson.start.weekday()
            days.setdefault(weekday, []).append(lesson)

        row = 0
        for weekday in sorted(days.keys()):
            # En-tête du jour
            day_date = self._current_monday + timedelta(days=weekday)
            header = ctk.CTkLabel(
                self._scroll,
                text=f"  {JOURS[weekday]}  {day_date.strftime('%d/%m')}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
                fg_color=("gray85", "gray25"),
                corner_radius=6,
            )
            header.grid(row=row, column=0, padx=4, pady=(12, 4), sticky="ew")
            row += 1

            for lesson in days[weekday]:
                card = self._make_lesson_card(lesson)
                card.grid(row=row, column=0, padx=4, pady=2, sticky="ew")
                row += 1

    def _make_lesson_card(self, lesson) -> ctk.CTkFrame:
        """Crée une carte pour un cours."""
        statut = ""
        if getattr(lesson, "canceled", False):
            statut = "Annulé"
        elif getattr(lesson, "teacher_absent", False):
            statut = "Absent"

        color = COULEUR_STATUT.get(statut, "#2ecc71")

        frame = ctk.CTkFrame(self._scroll, corner_radius=8, border_width=2, border_color=color)
        frame.grid_columnconfigure(1, weight=1)

        # Bande colorée gauche
        ctk.CTkFrame(frame, width=6, fg_color=color, corner_radius=6).grid(
            row=0, column=0, rowspan=2, padx=(4, 8), pady=4, sticky="ns"
        )

        subject = getattr(lesson, "subject", None)
        subject_name = subject.name if subject else "Matière inconnue"

        time_str = f"{lesson.start.strftime('%H:%M')} → {lesson.end.strftime('%H:%M')}"
        teacher = getattr(lesson, "teacher_name", "") or ""
        classroom = getattr(lesson, "classroom", "") or ""

        ctk.CTkLabel(
            frame,
            text=subject_name + (f"  ⚠ {statut}" if statut else ""),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, padx=4, pady=(6, 0), sticky="w")

        detail = f"{time_str}"
        if teacher:
            detail += f"  •  {teacher}"
        if classroom:
            detail += f"  •  Salle {classroom}"

        ctk.CTkLabel(
            frame,
            text=detail,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
        ).grid(row=1, column=1, padx=4, pady=(0, 6), sticky="w")

        return frame

    def _clear_lessons(self) -> None:
        for widget in self._scroll.winfo_children():
            if widget is not self._lbl_info:
                widget.destroy()

    def _show_error(self, message: str) -> None:
        self._lbl_info.configure(text=f"⚠ {message}", text_color="red")
        self._lbl_info.grid(row=0, column=0, pady=20)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_monday(d: date) -> date:
        return d - timedelta(days=d.weekday())
