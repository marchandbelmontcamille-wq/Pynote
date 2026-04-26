"""
Vue Emploi du temps — grille calendrier style Pronote.
Colonnes = jours, lignes = heures, cours positionnés selon heure réelle.
"""

import logging
import threading
import tkinter as tk
from datetime import date, timedelta, datetime

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.edt")

C = {
    "bg":        "#0f1117",
    "card":      "#1c2333",
    "border":    "#2a3347",
    "accent":    "#4f8ef7",
    "text":      "#e8eaf0",
    "subtext":   "#8892a4",
    "grid_line": "#1e2740",
    "header":    "#161b27",
    "today_col": "#1a2540",
    "hour_text": "#8892a4",
    "canceled":  "#e05252",
}

SUBJECT_COLORS = [
    "#4f8ef7", "#7c5cbf", "#3dd68c", "#f5a623",
    "#e05252", "#00bcd4", "#ff7043", "#ab47bc",
]

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

# Plage horaire affichée
HOUR_START = 7     # 7h
HOUR_END   = 19    # 19h

# Dimensions de la grille (pixels)
HEADER_H  = 36    # hauteur en-tête jours
HOUR_W    = 52    # largeur colonne heures
HOUR_H    = 56    # hauteur par heure
COL_W     = 140   # largeur par colonne jour
COL_GAP   = 2     # espacement entre colonnes


def _subject_color(name: str) -> str:
    return SUBJECT_COLORS[hash(name) % len(SUBJECT_COLORS)]


def _minutes_from_midnight(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


class EdtView(ctk.CTkFrame):
    def __init__(self, master, service: PronoteService) -> None:
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self._service = service
        self._current_monday = date.today() - timedelta(days=date.today().weekday())
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Barre supérieure
        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(topbar, text="Emploi du temps",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C["text"]).grid(row=0, column=0, sticky="w")

        nav = ctk.CTkFrame(topbar, fg_color="transparent")
        nav.grid(row=0, column=1)

        self._btn_prev = ctk.CTkButton(
            nav, text="◀", width=32, height=32, corner_radius=6,
            fg_color=C["card"], hover_color=C["border"],
            font=ctk.CTkFont(size=13), command=self._prev_week,
        )
        self._btn_prev.grid(row=0, column=0, padx=4)

        self._lbl_semaine = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["text"], width=220,
        )
        self._lbl_semaine.grid(row=0, column=1)

        self._btn_next = ctk.CTkButton(
            nav, text="▶", width=32, height=32, corner_radius=6,
            fg_color=C["card"], hover_color=C["border"],
            font=ctk.CTkFont(size=13), command=self._next_week,
        )
        self._btn_next.grid(row=0, column=2, padx=4)

        ctk.CTkButton(
            topbar, text="Aujourd'hui", width=100, height=32,
            corner_radius=6, fg_color=C["accent"], hover_color="#3a73d4",
            font=ctk.CTkFont(size=12), command=self._go_today,
        ).grid(row=0, column=2, sticky="e")

        # Zone scrollable pour le canvas
        self._scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=C["bg"],
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"],
        )
        self._scroll_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll_frame.grid_columnconfigure(0, weight=1)

        # Label info (chargement / erreur)
        self._lbl_info = ctk.CTkLabel(
            self._scroll_frame, text="Chargement…",
            font=ctk.CTkFont(size=14), text_color=C["subtext"],
        )
        self._lbl_info.grid(row=0, column=0, pady=40)

        # Canvas pour la grille
        total_h = HEADER_H + (HOUR_END - HOUR_START) * HOUR_H
        self._nb_days = 5  # sera mis à jour selon les données
        total_w = HOUR_W + self._nb_days * (COL_W + COL_GAP)
        self._canvas = tk.Canvas(
            self._scroll_frame,
            bg=C["bg"],
            highlightthickness=0,
            width=total_w,
            height=total_h,
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _prev_week(self) -> None:
        self._current_monday -= timedelta(weeks=1)
        self.refresh()

    def _next_week(self) -> None:
        self._current_monday += timedelta(weeks=1)
        self.refresh()

    def _go_today(self) -> None:
        self._current_monday = date.today() - timedelta(days=date.today().weekday())
        self.refresh()

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        sunday = self._current_monday + timedelta(days=6)
        self._lbl_semaine.configure(
            text=f"{self._current_monday.strftime('%d %b')}  →  {sunday.strftime('%d %b %Y')}"
        )
        self._canvas.grid_remove()
        self._lbl_info.configure(text="Chargement…", text_color=C["subtext"])
        self._lbl_info.grid(row=0, column=0, pady=40)
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            lessons = self._service.get_timetable(self._current_monday)
            self.after(0, lambda: self._draw_grid(lessons))
        except Exception as exc:
            msg = str(exc) if config.IS_DEV else "Impossible de charger l'emploi du temps."
            self.after(0, lambda: self._show_info(f"⚠  {msg}", error=True))

    # ------------------------------------------------------------------
    # Dessin de la grille
    # ------------------------------------------------------------------

    def _draw_grid(self, lessons: list) -> None:
        self._lbl_info.grid_remove()
        c = self._canvas
        c.delete("all")

        # Déterminer le nombre de jours à afficher
        if not lessons:
            nb_days = 5
        else:
            max_weekday = max(l.start.weekday() for l in lessons)
            nb_days = max(5, max_weekday + 1)

        total_w = HOUR_W + nb_days * (COL_W + COL_GAP)
        total_h = HEADER_H + (HOUR_END - HOUR_START) * HOUR_H
        c.configure(width=total_w, height=total_h)
        c.grid(row=0, column=0, sticky="nw")

        today = date.today()

        # ── En-têtes des jours ──
        for i in range(nb_days):
            x0 = HOUR_W + i * (COL_W + COL_GAP)
            x1 = x0 + COL_W
            day_date = self._current_monday + timedelta(days=i)
            is_today = day_date == today
            bg = C["accent"] if is_today else C["header"]
            c.create_rectangle(x0, 0, x1, HEADER_H, fill=bg, outline="")
            label = f"{JOURS[i]}  {day_date.strftime('%d/%m')}"
            c.create_text(
                (x0 + x1) // 2, HEADER_H // 2,
                text=label,
                fill="#ffffff" if is_today else C["subtext"],
                font=("Segoe UI", 9, "bold"),
                anchor="center",
            )

        # ── Colonnes de fond ──
        for i in range(nb_days):
            x0 = HOUR_W + i * (COL_W + COL_GAP)
            x1 = x0 + COL_W
            day_date = self._current_monday + timedelta(days=i)
            col_bg = C["today_col"] if day_date == today else C["card"]
            c.create_rectangle(x0, HEADER_H, x1, total_h, fill=col_bg, outline="")

        # ── Lignes horaires ──
        for h in range(HOUR_START, HOUR_END + 1):
            y = HEADER_H + (h - HOUR_START) * HOUR_H
            # Ligne horizontale
            c.create_line(HOUR_W, y, total_w, y, fill=C["grid_line"], width=1)
            # Label heure
            c.create_text(
                HOUR_W - 6, y,
                text=f"{h:02d}:00",
                fill=C["hour_text"],
                font=("Segoe UI", 8),
                anchor="e",
            )

        # ── Cours ──
        if not lessons:
            c.create_text(
                total_w // 2, total_h // 2,
                text="Aucun cours cette semaine",
                fill=C["subtext"],
                font=("Segoe UI", 11),
                anchor="center",
            )
        else:
            self._draw_lessons(c, lessons)

    def _draw_lessons(self, c: tk.Canvas, lessons: list) -> None:
        total_minutes = (HOUR_END - HOUR_START) * 60

        for lesson in lessons:
            weekday = lesson.start.weekday()
            start_min = _minutes_from_midnight(lesson.start) - HOUR_START * 60
            end_min   = _minutes_from_midnight(lesson.end)   - HOUR_START * 60

            # Clamp
            start_min = max(0, min(start_min, total_minutes))
            end_min   = max(0, min(end_min,   total_minutes))
            if end_min <= start_min:
                continue

            x0 = HOUR_W + weekday * (COL_W + COL_GAP) + 2
            x1 = x0 + COL_W - 4
            y0 = HEADER_H + int(start_min / 60 * HOUR_H) + 1
            y1 = HEADER_H + int(end_min   / 60 * HOUR_H) - 1

            canceled = getattr(lesson, "canceled", False)
            teacher_absent = getattr(lesson, "teacher_absent", False)
            subject = getattr(lesson, "subject", None)
            name = subject.name if subject else "Matière"

            bg_color = C["canceled"] if (canceled or teacher_absent) else _subject_color(name)

            # Rectangle principal
            c.create_rectangle(x0, y0, x1, y1, fill=bg_color, outline="", tags="lesson")

            # Bande de titre
            title_h = min(18, y1 - y0)
            c.create_rectangle(x0, y0, x1, y0 + title_h,
                                fill=self._darken(bg_color), outline="", tags="lesson")

            # Texte matière
            height = y1 - y0
            short_name = name if len(name) <= 18 else name[:16] + "…"
            c.create_text(
                (x0 + x1) // 2, y0 + title_h // 2,
                text=short_name,
                fill="#ffffff",
                font=("Segoe UI", 8, "bold"),
                anchor="center",
                tags="lesson",
            )

            if height > 36:
                # Heure
                time_str = f"{lesson.start.strftime('%H:%M')}–{lesson.end.strftime('%H:%M')}"
                c.create_text(
                    (x0 + x1) // 2, y0 + title_h + 10,
                    text=time_str,
                    fill="white",
                    font=("Segoe UI", 7),
                    anchor="center",
                    tags="lesson",
                )

            if height > 52:
                teacher = getattr(lesson, "teacher_name", "") or ""
                classroom = getattr(lesson, "classroom", "") or ""
                detail = "\n".join(filter(None, [teacher, f"Salle {classroom}" if classroom else ""]))
                if detail:
                    c.create_text(
                        (x0 + x1) // 2, y0 + title_h + 24,
                        text=detail,
                        fill="white",
                        font=("Segoe UI", 7),
                        anchor="center",
                        tags="lesson",
                    )

    @staticmethod
    def _darken(hex_color: str) -> str:
        """Assombrit une couleur hex de ~20%."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = int(r * 0.7), int(g * 0.7), int(b * 0.7)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _show_info(self, msg: str, *, error: bool = False) -> None:
        self._canvas.grid_remove()
        self._lbl_info.configure(
            text=msg,
            text_color=C["canceled"] if error else C["subtext"],
        )
        self._lbl_info.grid(row=0, column=0, pady=40)
