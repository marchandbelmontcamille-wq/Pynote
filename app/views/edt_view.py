"""
Vue Emploi du temps — grille calendrier style moderne.
"""

import logging
import threading
import tkinter as tk
from datetime import date, timedelta, datetime

import customtkinter as ctk

import config
from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.edt")

# ── Palette ────────────────────────────────────────────────────────────
BG         = "#0f1117"
SIDEBAR_BG = "#161b27"
CARD_BG    = "#1a2035"
GRID_LINE  = "#1e2740"
HEADER_BG  = "#161b27"
TODAY_COL  = "#141e33"
HOUR_COLOR = "#4a5568"
TEXT_MAIN  = "#e8eaf0"
TEXT_SUB   = "#64748b"
ACCENT     = "#4f8ef7"

SUBJECT_COLORS = [
    ("#4f8ef7", "#1a3a6b"),  # bleu
    ("#7c5cbf", "#2e1f5e"),  # violet
    ("#3dd68c", "#0f4a2e"),  # vert
    ("#f59e0b", "#4a2d00"),  # orange
    ("#ef4444", "#4a0f0f"),  # rouge
    ("#06b6d4", "#063544"),  # cyan
    ("#f97316", "#4a1a00"),  # orange vif
    ("#a855f7", "#2e0a4a"),  # mauve
]

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

HOUR_START = 7
HOUR_END   = 19
HEADER_H   = 44
HOUR_W     = 48
HOUR_H     = 60
COL_W      = 148
COL_GAP    = 3


def _subject_colors(name: str):
    return SUBJECT_COLORS[hash(name) % len(SUBJECT_COLORS)]


def _round_rect(canvas: tk.Canvas, x0, y0, x1, y1, r=8, **kw):
    """Dessine un rectangle à coins arrondis."""
    pts = [
        x0+r, y0,  x1-r, y0,
        x1, y0,    x1, y0+r,
        x1, y1-r,  x1, y1,
        x1-r, y1,  x0+r, y1,
        x0, y1,    x0, y1-r,
        x0, y0+r,  x0, y0,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class EdtView(ctk.CTkFrame):
    def __init__(self, master, service: PronoteService) -> None:
        super().__init__(master, fg_color=BG, corner_radius=0)
        self._service = service
        self._current_monday = date.today() - timedelta(days=date.today().weekday())
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Topbar
        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            topbar, text="Emploi du temps",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w")

        nav = ctk.CTkFrame(topbar, fg_color="transparent")
        nav.grid(row=0, column=1)

        for col, (txt, cmd) in enumerate([("◀", self._prev_week), ("▶", self._next_week)]):
            ctk.CTkButton(
                nav, text=txt, width=30, height=30, corner_radius=6,
                fg_color=CARD_BG, hover_color=GRID_LINE,
                font=ctk.CTkFont(size=12), command=cmd,
                border_width=1, border_color=GRID_LINE,
            ).grid(row=0, column=col * 2, padx=3)

        self._lbl_semaine = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_MAIN, width=230,
        )
        self._lbl_semaine.grid(row=0, column=1, padx=6)

        ctk.CTkButton(
            topbar, text="Aujourd'hui", width=95, height=30,
            corner_radius=6, fg_color=ACCENT, hover_color="#3a73d4",
            font=ctk.CTkFont(size=11, weight="bold"), command=self._go_today,
        ).grid(row=0, column=2, sticky="e")

        # Scrollable
        self._sf = ctk.CTkScrollableFrame(
            self, fg_color=BG,
            scrollbar_button_color=GRID_LINE,
            scrollbar_button_hover_color=ACCENT,
        )
        self._sf.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self._sf.grid_columnconfigure(0, weight=1)

        self._lbl_info = ctk.CTkLabel(
            self._sf, text="Chargement…",
            font=ctk.CTkFont(size=13), text_color=TEXT_SUB,
        )
        self._lbl_info.grid(row=0, column=0, pady=40)

        total_h = HEADER_H + (HOUR_END - HOUR_START) * HOUR_H
        total_w = HOUR_W + 5 * (COL_W + COL_GAP)
        self._canvas = tk.Canvas(
            self._sf, bg=BG, highlightthickness=0,
            width=total_w, height=total_h,
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _prev_week(self):
        self._current_monday -= timedelta(weeks=1)
        self.refresh()

    def _next_week(self):
        self._current_monday += timedelta(weeks=1)
        self.refresh()

    def _go_today(self):
        self._current_monday = date.today() - timedelta(days=date.today().weekday())
        self.refresh()

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        sunday = self._current_monday + timedelta(days=6)
        self._lbl_semaine.configure(
            text=f"{self._current_monday.strftime('%d %b')}  —  {sunday.strftime('%d %b %Y')}"
        )
        self._canvas.grid_remove()
        self._lbl_info.configure(text="Chargement…", text_color=TEXT_SUB)
        self._lbl_info.grid(row=0, column=0, pady=40)
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            lessons = self._service.get_timetable(self._current_monday)
            self.after(0, lambda: self._draw(lessons))
        except Exception as exc:
            msg = str(exc) if config.IS_DEV else "Impossible de charger l'emploi du temps."
            self.after(0, lambda: self._show_info(f"⚠  {msg}", error=True))

    # ------------------------------------------------------------------
    # Dessin
    # ------------------------------------------------------------------

    def _draw(self, lessons: list) -> None:
        self._lbl_info.grid_remove()
        c = self._canvas
        c.delete("all")

        nb_days = 5
        if lessons:
            nb_days = max(5, max(l.start.weekday() for l in lessons) + 1)
            nb_days = min(nb_days, 6)

        total_w = HOUR_W + nb_days * (COL_W + COL_GAP)
        total_h = HEADER_H + (HOUR_END - HOUR_START) * HOUR_H
        c.configure(width=total_w, height=total_h)
        c.grid(row=0, column=0, sticky="nw")

        today = date.today()

        # ── Fond général ──
        c.create_rectangle(0, 0, total_w, total_h, fill=BG, outline="")

        # ── Colonnes de fond ──
        for i in range(nb_days):
            x0 = HOUR_W + i * (COL_W + COL_GAP)
            x1 = x0 + COL_W
            day_date = self._current_monday + timedelta(days=i)
            col_bg = TODAY_COL if day_date == today else CARD_BG
            c.create_rectangle(x0, HEADER_H, x1, total_h, fill=col_bg, outline="")

        # ── Lignes horaires ──
        for h in range(HOUR_START, HOUR_END + 1):
            y = HEADER_H + (h - HOUR_START) * HOUR_H
            # Ligne pleine
            c.create_line(HOUR_W, y, total_w, y, fill=GRID_LINE, width=1)
            # Demi-heure (pointillé léger)
            y_half = y + HOUR_H // 2
            if h < HOUR_END:
                c.create_line(HOUR_W, y_half, total_w, y_half,
                              fill=GRID_LINE, width=1, dash=(2, 6))
            # Label heure
            c.create_text(
                HOUR_W - 8, y + 4,
                text=f"{h:02d}:00",
                fill=HOUR_COLOR,
                font=("Segoe UI", 8),
                anchor="ne",
            )

        # ── Lignes verticales entre colonnes ──
        for i in range(nb_days + 1):
            x = HOUR_W + i * (COL_W + COL_GAP)
            c.create_line(x, HEADER_H, x, total_h, fill=GRID_LINE, width=1)

        # ── En-têtes des jours ──
        c.create_rectangle(0, 0, total_w, HEADER_H, fill=HEADER_BG, outline="")
        c.create_line(0, HEADER_H, total_w, HEADER_H, fill=GRID_LINE, width=1)

        for i in range(nb_days):
            x0 = HOUR_W + i * (COL_W + COL_GAP)
            x1 = x0 + COL_W
            day_date = self._current_monday + timedelta(days=i)
            is_today = day_date == today

            if is_today:
                # Pill bleu pour aujourd'hui
                _round_rect(c, x0 + 12, 6, x1 - 12, HEADER_H - 6,
                            r=10, fill=ACCENT, outline="")
                color = "#ffffff"
            else:
                color = TEXT_SUB

            jour = JOURS[i]
            num  = day_date.strftime("%d")
            cx   = (x0 + x1) // 2
            c.create_text(cx, HEADER_H // 2 - 6, text=jour.upper()[:3],
                          fill=color, font=("Segoe UI", 7, "bold"), anchor="center")
            c.create_text(cx, HEADER_H // 2 + 6, text=num,
                          fill=color, font=("Segoe UI", 10, "bold"), anchor="center")

        # ── Ligne de l'heure actuelle ──
        if self._current_monday <= today <= self._current_monday + timedelta(days=nb_days - 1):
            now = datetime.now()
            mins = (now.hour - HOUR_START) * 60 + now.minute
            if 0 <= mins <= (HOUR_END - HOUR_START) * 60:
                y_now = HEADER_H + int(mins / 60 * HOUR_H)
                wd = today.weekday()
                x0 = HOUR_W + wd * (COL_W + COL_GAP)
                x1 = x0 + COL_W
                c.create_oval(HOUR_W - 5, y_now - 4, HOUR_W + 5, y_now + 4,
                              fill=ACCENT, outline="")
                c.create_line(HOUR_W, y_now, total_w, y_now,
                              fill=ACCENT, width=2)

        # ── Cours ──
        if not lessons:
            c.create_text(
                total_w // 2, total_h // 2,
                text="Aucun cours cette semaine",
                fill=TEXT_SUB, font=("Segoe UI", 12), anchor="center",
            )
        else:
            self._draw_lessons(c, lessons)

    def _draw_lessons(self, c: tk.Canvas, lessons: list) -> None:
        total_mins = (HOUR_END - HOUR_START) * 60

        for lesson in lessons:
            wd = lesson.start.weekday()
            if wd >= 6:
                continue

            s_min = lesson.start.hour * 60 + lesson.start.minute - HOUR_START * 60
            e_min = lesson.end.hour   * 60 + lesson.end.minute   - HOUR_START * 60
            s_min = max(0, min(s_min, total_mins))
            e_min = max(0, min(e_min, total_mins))
            if e_min <= s_min:
                continue

            x0 = HOUR_W + wd * (COL_W + COL_GAP) + 3
            x1 = x0 + COL_W - 6
            y0 = HEADER_H + int(s_min / 60 * HOUR_H) + 2
            y1 = HEADER_H + int(e_min / 60 * HOUR_H) - 2
            h  = y1 - y0

            canceled = getattr(lesson, "canceled", False)
            teacher_absent = getattr(lesson, "teacher_absent", False)
            subject = getattr(lesson, "subject", None)
            name = subject.name if subject else "Matière"

            if canceled or teacher_absent:
                fg, bg = "#ef4444", "#1a0a0a"
            else:
                fg, bg = _subject_colors(name)

            # Rectangle principal arrondi
            _round_rect(c, x0, y0, x1, y1, r=6, fill=bg, outline=fg, width=1)

            # Barre colorée gauche
            _round_rect(c, x0, y0, x0 + 4, y1, r=3, fill=fg, outline="")

            # Texte matière
            short = name if len(name) <= 16 else name[:14] + "…"
            if canceled:
                short += " ✕"
            elif teacher_absent:
                short += " ⚠"

            text_x = x0 + 10
            cx = (x0 + x1) // 2

            c.create_text(
                text_x, y0 + 10,
                text=short,
                fill=fg,
                font=("Segoe UI", 8, "bold"),
                anchor="w",
            )

            if h > 32:
                time_str = f"{lesson.start.strftime('%H:%M')} – {lesson.end.strftime('%H:%M')}"
                c.create_text(
                    text_x, y0 + 22,
                    text=time_str,
                    fill=self._blend(fg, 0.6),
                    font=("Segoe UI", 7),
                    anchor="w",
                )

            if h > 48:
                teacher = getattr(lesson, "teacher_name", "") or ""
                if teacher:
                    c.create_text(
                        text_x, y0 + 32,
                        text=teacher,
                        fill=self._blend(fg, 0.5),
                        font=("Segoe UI", 7),
                        anchor="w",
                    )

            if h > 64:
                classroom = getattr(lesson, "classroom", "") or ""
                if classroom:
                    c.create_text(
                        text_x, y0 + 42,
                        text=f"Salle {classroom}",
                        fill=self._blend(fg, 0.45),
                        font=("Segoe UI", 7),
                        anchor="w",
                    )

    @staticmethod
    def _blend(hex_color: str, factor: float) -> str:
        """Mélange une couleur avec le fond sombre."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        br, bg_c, bb = 0x0f, 0x11, 0x17
        r = int(r * factor + br * (1 - factor))
        g = int(g * factor + bg_c * (1 - factor))
        b = int(b * factor + bb * (1 - factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _show_info(self, msg: str, *, error: bool = False) -> None:
        self._canvas.grid_remove()
        self._lbl_info.configure(
            text=msg,
            text_color="#ef4444" if error else TEXT_SUB,
        )
        self._lbl_info.grid(row=0, column=0, pady=40)
