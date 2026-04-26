"""
Vue Emploi du temps — design refait.
"""

import logging
import threading
from datetime import date, timedelta

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.edt")

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
    "day_head": "#161b27",
}

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# Couleurs par matière (rotation)
SUBJECT_COLORS = [
    "#4f8ef7", "#7c5cbf", "#3dd68c", "#f5a623",
    "#e05252", "#00bcd4", "#ff7043", "#ab47bc",
]


def _subject_color(name: str) -> str:
    return SUBJECT_COLORS[hash(name) % len(SUBJECT_COLORS)]


class EdtView(ctk.CTkFrame):
    def __init__(self, master, service: PronoteService) -> None:
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self._service = service
        self._current_monday = date.today() - timedelta(days=date.today().weekday())
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # ── Barre supérieure ──
        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.grid(row=0, column=0, padx=24, pady=(20, 12), sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            topbar,
            text="Emploi du temps",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, sticky="w")

        # Navigation semaine (centré)
        nav = ctk.CTkFrame(topbar, fg_color="transparent")
        nav.grid(row=0, column=1)

        self._btn_prev = ctk.CTkButton(
            nav, text="◀", width=36, height=36, corner_radius=8,
            fg_color=C["card"], hover_color=C["card2"],
            border_width=1, border_color=C["border"],
            font=ctk.CTkFont(size=14), command=self._prev_week,
        )
        self._btn_prev.grid(row=0, column=0, padx=4)

        self._lbl_semaine = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C["text"], width=260,
        )
        self._lbl_semaine.grid(row=0, column=1, padx=8)

        self._btn_next = ctk.CTkButton(
            nav, text="▶", width=36, height=36, corner_radius=8,
            fg_color=C["card"], hover_color=C["card2"],
            border_width=1, border_color=C["border"],
            font=ctk.CTkFont(size=14), command=self._next_week,
        )
        self._btn_next.grid(row=0, column=2, padx=4)

        # Bouton aujourd'hui
        ctk.CTkButton(
            topbar, text="Aujourd'hui", width=100, height=36,
            corner_radius=8, fg_color=C["accent"], hover_color="#3a73d4",
            font=ctk.CTkFont(size=12),
            command=self._go_today,
        ).grid(row=0, column=2, sticky="e")

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

    def _prev_week(self) -> None:
        self._current_monday -= timedelta(weeks=1)
        self.refresh()

    def _next_week(self) -> None:
        self._current_monday += timedelta(weeks=1)
        self.refresh()

    def _go_today(self) -> None:
        self._current_monday = date.today() - timedelta(days=date.today().weekday())
        self.refresh()

    def refresh(self) -> None:
        sunday = self._current_monday + timedelta(days=6)
        self._lbl_semaine.configure(
            text=f"{self._current_monday.strftime('%d %b')}  →  {sunday.strftime('%d %b %Y')}"
        )
        self._clear_lessons()
        self._lbl_info.configure(text="Chargement…", text_color=C["subtext"])
        self._lbl_info.grid(row=0, column=0, pady=40)
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            lessons = self._service.get_timetable(self._current_monday)
            self.after(0, lambda: self._display_lessons(lessons))
        except Exception as exc:
            msg = str(exc) if config.IS_DEV else "Impossible de charger l'emploi du temps."
            self.after(0, lambda: self._show_info(f"⚠  {msg}", error=True))

    def _display_lessons(self, lessons: list) -> None:
        self._lbl_info.grid_remove()
        self._clear_lessons()

        if not lessons:
            self._show_info("Aucun cours cette semaine.", error=False)
            return

        days: dict[int, list] = {}
        for lesson in lessons:
            days.setdefault(lesson.start.weekday(), []).append(lesson)

        row = 0
        for weekday in sorted(days.keys()):
            day_date = self._current_monday + timedelta(days=weekday)
            is_today = day_date == date.today()

            # En-tête de jour
            day_frame = ctk.CTkFrame(
                self._scroll,
                fg_color=C["accent"] if is_today else C["day_head"],
                corner_radius=10,
            )
            day_frame.grid(row=row, column=0, sticky="ew", pady=(14, 4))
            ctk.CTkLabel(
                day_frame,
                text=f"  {JOURS[weekday]}  {day_date.strftime('%d %B')}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#ffffff" if is_today else C["text"],
                anchor="w",
            ).grid(row=0, column=0, padx=12, pady=6, sticky="w")
            row += 1

            for lesson in days[weekday]:
                card = self._make_lesson_card(lesson)
                card.grid(row=row, column=0, sticky="ew", pady=2)
                row += 1

    def _make_lesson_card(self, lesson) -> ctk.CTkFrame:
        canceled = getattr(lesson, "canceled", False)
        teacher_absent = getattr(lesson, "teacher_absent", False)

        subject = getattr(lesson, "subject", None)
        name = subject.name if subject else "Matière inconnue"
        color = _subject_color(name)
        if canceled or teacher_absent:
            color = C["danger"]

        frame = ctk.CTkFrame(
            self._scroll,
            fg_color=C["card"],
            corner_radius=10,
            border_width=0,
        )
        frame.grid_columnconfigure(1, weight=1)

        # Bande de couleur gauche
        ctk.CTkFrame(
            frame, width=4, fg_color=color, corner_radius=4
        ).grid(row=0, column=0, rowspan=2, padx=(6, 10), pady=8, sticky="ns")

        # Heure
        time_str = f"{lesson.start.strftime('%H:%M')} – {lesson.end.strftime('%H:%M')}"
        ctk.CTkLabel(
            frame,
            text=time_str,
            font=ctk.CTkFont(size=11),
            text_color=C["subtext"],
            width=90,
            anchor="w",
        ).grid(row=0, column=1, padx=(0, 8), pady=(8, 0), sticky="w")

        # Matière
        title = name
        if canceled:
            title += "  —  🚫 Cours annulé"
        elif teacher_absent:
            title += "  —  ⚠ Prof absent"

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C["danger"] if (canceled or teacher_absent) else C["text"],
            anchor="w",
        ).grid(row=1, column=1, padx=(0, 8), pady=(0, 8), sticky="w")

        # Détails (prof + salle)
        teacher = getattr(lesson, "teacher_name", "") or ""
        classroom = getattr(lesson, "classroom", "") or ""
        details = "  ·  ".join(filter(None, [teacher, f"Salle {classroom}" if classroom else ""]))
        if details:
            ctk.CTkLabel(
                frame,
                text=details,
                font=ctk.CTkFont(size=11),
                text_color=C["subtext"],
                anchor="e",
            ).grid(row=0, column=2, padx=(0, 14), pady=(8, 0), sticky="e")

        return frame

    def _clear_lessons(self) -> None:
        for w in self._scroll.winfo_children():
            if w is not self._lbl_info:
                w.destroy()

    def _show_info(self, msg: str, *, error: bool = False) -> None:
        self._lbl_info.configure(
            text=msg,
            text_color=C["danger"] if error else C["subtext"],
        )
        self._lbl_info.grid(row=0, column=0, pady=40)
