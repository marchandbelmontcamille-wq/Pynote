"""
Vue Notes — notes + moyennes par période (trimestre ou semestre).
Chargement automatique au login, sélecteur de période, moyennes établissement.
"""

import threading
import logging
import customtkinter as ctk

from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.notes")

C = {
    "bg":      "#0f1117",
    "card":    "#1c2333",
    "border":  "#2a3347",
    "accent":  "#4f8ef7",
    "accent2": "#7c5cbf",
    "text":    "#e8eaf0",
    "subtext": "#8892a4",
    "success": "#3dd68c",
    "warning": "#f5a623",
    "danger":  "#e05252",
    "avg_bg":  "#141929",
}

MOIS_FR = {
    1: "janv.", 2: "févr.", 3: "mars", 4: "avr.",
    5: "mai",  6: "juin",  7: "juil.", 8: "août",
    9: "sept.", 10: "oct.", 11: "nov.", 12: "déc.",
}


def _date_fr(d) -> str:
    if d is None:
        return "—"
    try:
        return f"{d.day} {MOIS_FR.get(d.month, '')} {d.year}"
    except Exception:
        return str(d)


def _note_color(val: float, out_of: float) -> str:
    if out_of <= 0:
        return C["text"]
    ratio = val / out_of
    if ratio >= 0.75:
        return C["success"]
    if ratio >= 0.50:
        return C["warning"]
    return C["danger"]


def _fmt_avg(val) -> str:
    """Formate une moyenne (str ou float) de façon homogène."""
    if val is None:
        return "—"
    try:
        return f"{float(str(val).replace(',', '.')):.2f}"
    except Exception:
        return str(val)


class NotesView(ctk.CTkFrame):
    def __init__(self, master, service: PronoteService) -> None:
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self._service   = service
        self._periods   = []          # liste des Period
        self._period_idx = 0          # index courant
        self._period_var = ctk.StringVar(value="")
        self._build_ui()

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── En-tête ───────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="📊  Notes",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, padx=24, sticky="w")

        # Sélecteur de période (rempli après chargement)
        self._period_menu = ctk.CTkOptionMenu(
            header,
            variable=self._period_var,
            values=["Chargement…"],
            width=200, height=30,
            font=ctk.CTkFont(size=11),
            fg_color=C["border"],
            button_color=C["accent"],
            button_hover_color="#3a6fd8",
            command=self._on_period_change,
        )
        self._period_menu.grid(row=0, column=1, padx=8)

        ctk.CTkButton(
            header,
            text="↻",
            width=36, height=30,
            font=ctk.CTkFont(size=14),
            fg_color=C["accent"],
            hover_color="#3a6fd8",
            corner_radius=6,
            command=self._reload_current,
        ).grid(row=0, column=2, padx=(0, 16))

        # ── Bandeau moyennes générales ─────────────────────────────────
        self._avg_bar = ctk.CTkFrame(self, fg_color=C["avg_bg"], corner_radius=0, height=44)
        self._avg_bar.grid(row=1, column=0, sticky="ew")
        self._avg_bar.grid_columnconfigure((0, 1, 2), weight=1)
        self._avg_bar.grid_propagate(False)

        self._lbl_avg_me    = ctk.CTkLabel(self._avg_bar, text="Moy. générale : —",
                                            font=ctk.CTkFont(size=12, weight="bold"),
                                            text_color=C["text"])
        self._lbl_avg_me.grid(row=0, column=0, padx=24, sticky="w")

        self._lbl_avg_class = ctk.CTkLabel(self._avg_bar, text="Moy. classe : —",
                                            font=ctk.CTkFont(size=12),
                                            text_color=C["subtext"])
        self._lbl_avg_class.grid(row=0, column=1, padx=8, sticky="w")

        # ── Zone défilement ───────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"], corner_radius=0)
        self._scroll.grid(row=2, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._show_info("Chargement des notes…")

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Appelé au login (auto) ou sur ↻."""
        self._show_info("Chargement des périodes…")
        threading.Thread(target=self._load_periods_thread, daemon=True).start()

    def _load_periods_thread(self) -> None:
        try:
            periods = self._service.get_periods()
            current = self._service.get_current_period()
            self.after(0, self._on_periods_loaded, periods, current)
        except Exception as exc:
            self.after(0, self._show_info, f"Erreur : {exc}", True)

    def _on_periods_loaded(self, periods, current) -> None:
        self._periods = periods
        if not periods:
            self._show_info("Aucune période disponible.")
            return

        names = [p.name for p in periods]
        self._period_menu.configure(values=names)

        # Sélectionner la période courante par défaut
        idx = 0
        if current:
            for i, p in enumerate(periods):
                if p.id == current.id or p.name == current.name:
                    idx = i
                    break
        self._period_idx = idx
        self._period_var.set(names[idx])
        self._load_period(self._periods[idx])

    def _on_period_change(self, name: str) -> None:
        for i, p in enumerate(self._periods):
            if p.name == name:
                self._period_idx = i
                self._load_period(p)
                return

    def _reload_current(self) -> None:
        if self._periods:
            self._load_period(self._periods[self._period_idx])
        else:
            self.refresh()

    def _load_period(self, period) -> None:
        self._show_info("Chargement…")
        self._lbl_avg_me.configure(text="Moy. générale : …")
        self._lbl_avg_class.configure(text="Moy. classe : …")
        threading.Thread(target=self._load_data_thread, args=(period,), daemon=True).start()

    def _load_data_thread(self, period) -> None:
        try:
            grades   = self._service.get_grades(period)
            averages = self._service.get_averages(period)
            overall  = self._service.get_overall_average(period)
            cls_avg  = self._service.get_class_overall_average(period)
            self.after(0, self._display_all, grades, averages, overall, cls_avg)
        except Exception as exc:
            self.after(0, self._show_info, f"Erreur : {exc}", True)

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------

    def _display_all(self, grades, averages, overall, cls_avg) -> None:
        # Moyennes générales
        self._lbl_avg_me.configure(
            text=f"Moy. générale : {_fmt_avg(overall)}",
            text_color=C["success"] if overall else C["subtext"],
        )
        self._lbl_avg_class.configure(
            text=f"Moy. classe : {_fmt_avg(cls_avg)}",
        )

        # Construire un dict matière → Average
        avg_by_subj: dict[str, object] = {}
        for av in averages:
            subj = getattr(av, "subject", None)
            name = getattr(subj, "name", "?") if subj else "?"
            avg_by_subj[name] = av

        # Regrouper les notes par matière
        by_subject: dict[str, list] = {}
        for g in grades:
            subj = getattr(g, "subject", None)
            name = getattr(subj, "name", "Matière inconnue") if subj else "Matière inconnue"
            by_subject.setdefault(name, []).append(g)

        # Ajouter les matières avec moyenne mais sans note individuelle
        for name in avg_by_subj:
            by_subject.setdefault(name, [])

        self._clear_cards()
        if not by_subject:
            self._show_info("Aucune note pour cette période.")
            return

        row = 0
        for subject in sorted(by_subject.keys()):
            av = avg_by_subj.get(subject)
            row = self._render_subject(subject, by_subject[subject], av, row)

    def _render_subject(self, subject: str, items: list, av, start_row: int) -> int:
        row = start_row

        # En-tête matière avec moyennes
        subj_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        subj_frame.grid(row=row, column=0, sticky="ew", padx=20, pady=(14, 2))
        subj_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            subj_frame,
            text=subject,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["accent"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if av is not None:
            me_str  = _fmt_avg(getattr(av, "student", None))
            cl_str  = _fmt_avg(getattr(av, "class_average", None))
            out_str = _fmt_avg(getattr(av, "out_of", None))
            avg_txt = f"Moy. élève : {me_str}/{out_str}   Moy. classe : {cl_str}/{out_str}"
            try:
                me_f  = float(str(getattr(av, "student", 0)).replace(",", "."))
                out_f = float(str(getattr(av, "out_of", 20)).replace(",", ".")) or 20
                color = _note_color(me_f, out_f)
            except Exception:
                color = C["subtext"]
            ctk.CTkLabel(
                subj_frame,
                text=avg_txt,
                font=ctk.CTkFont(size=10),
                text_color=color,
                anchor="w",
            ).grid(row=1, column=0, sticky="w")

        row += 1

        for g in items:
            card = self._make_grade_card(g)
            card.grid(row=row, column=0, sticky="ew", padx=16, pady=2)
            row += 1

        return row

    def _make_grade_card(self, g) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=C["card"],
            corner_radius=8,
            border_width=1,
            border_color=C["border"],
        )
        card.grid_columnconfigure(1, weight=1)

        try:
            val   = float(str(g.grade).replace(",", "."))
            out   = float(str(g.out_of).replace(",", "."))
            color = _note_color(val, out)
            note_txt = f"{g.grade}/{g.out_of}"
        except Exception:
            color    = C["subtext"]
            note_txt = str(getattr(g, "grade", "—"))

        ctk.CTkLabel(
            card, text=note_txt,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=color, width=90, anchor="center",
        ).grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=8)

        comment = getattr(g, "comment", "") or ""
        ctk.CTkLabel(
            card, text=comment if comment else "—",
            font=ctk.CTkFont(size=11),
            text_color=C["text"], anchor="w", wraplength=420,
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(8, 0))

        date_str = _date_fr(getattr(g, "date", None))
        coeff    = getattr(g, "coefficient", None)
        meta     = f"Le {date_str}"
        if coeff is not None:
            meta += f"  •  coeff. {coeff}"
        ctk.CTkLabel(
            card, text=meta,
            font=ctk.CTkFont(size=10), text_color=C["subtext"], anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=4, pady=(0, 8))

        return card

    def _clear_cards(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

    def _show_info(self, msg: str, *, error: bool = False) -> None:
        self._clear_cards()
        ctk.CTkLabel(
            self._scroll, text=msg,
            font=ctk.CTkFont(size=13),
            text_color=C["danger"] if error else C["subtext"],
            wraplength=500,
        ).grid(row=0, column=0, pady=40, padx=20)
