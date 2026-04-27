"""
Vue Notes — affiche les notes du trimestre courant.
"""

import threading
import logging
import customtkinter as ctk

from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.notes")

# Palette (même que app.py)
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
    """Couleur selon le ratio note/sur."""
    if out_of <= 0:
        return C["text"]
    ratio = val / out_of
    if ratio >= 0.75:
        return C["success"]
    if ratio >= 0.50:
        return C["warning"]
    return C["danger"]


class NotesView(ctk.CTkFrame):
    def __init__(self, master, service: PronoteService) -> None:
        super().__init__(master, fg_color=C["bg"], corner_radius=0)
        self._service = service
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
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
            text="📊  Notes",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, padx=24, sticky="w")

        ctk.CTkButton(
            header,
            text="↻  Actualiser",
            width=110, height=30,
            font=ctk.CTkFont(size=11),
            fg_color=C["accent"],
            hover_color="#3a6fd8",
            corner_radius=6,
            command=self.refresh,
        ).grid(row=0, column=1, padx=16)

        # ── Zone de défilement ────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=C["bg"], corner_radius=0,
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._scroll.grid_columnconfigure(0, weight=1)

        self._show_info("Cliquez sur ↻ Actualiser pour charger les notes.")

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        self._clear_cards()
        self._show_info("Chargement…")
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            grades = self._service.get_grades()
            self.after(0, self._display_grades, grades)
        except Exception as exc:
            self.after(0, self._show_info, f"Erreur : {exc}", True)

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------

    def _display_grades(self, grades: list) -> None:
        self._clear_cards()
        if not grades:
            self._show_info("Aucune note disponible pour le moment.")
            return

        # Regrouper par matière
        by_subject: dict[str, list] = {}
        for g in grades:
            subj = getattr(g, "subject", None)
            subj_name = getattr(subj, "name", "Matière inconnue") if subj else "Matière inconnue"
            by_subject.setdefault(subj_name, []).append(g)

        for row_idx, (subject, items) in enumerate(sorted(by_subject.items())):
            # En-tête matière
            ctk.CTkLabel(
                self._scroll,
                text=subject,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=C["accent"],
                anchor="w",
            ).grid(row=row_idx * 10, column=0, sticky="w", padx=20, pady=(14, 2))

            for sub_idx, g in enumerate(items):
                self._scroll.grid_columnconfigure(0, weight=1)
                card = self._make_grade_card(g)
                card.grid(
                    row=row_idx * 10 + sub_idx + 1,
                    column=0, sticky="ew",
                    padx=16, pady=2,
                )

    def _make_grade_card(self, g) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=C["card"],
            corner_radius=8,
            border_width=1,
            border_color=C["border"],
        )
        card.grid_columnconfigure(1, weight=1)

        # Valeur numérique
        try:
            val   = float(str(g.grade).replace(",", "."))
            out   = float(str(g.out_of).replace(",", "."))
            color = _note_color(val, out)
            note_txt = f"{g.grade}/{g.out_of}"
        except Exception:
            color    = C["subtext"]
            note_txt = str(getattr(g, "grade", "—"))

        ctk.CTkLabel(
            card,
            text=note_txt,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=color,
            width=90,
            anchor="center",
        ).grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=8)

        # Commentaire / description
        comment = getattr(g, "comment", "") or ""
        ctk.CTkLabel(
            card,
            text=comment if comment else "—",
            font=ctk.CTkFont(size=11),
            text_color=C["text"],
            anchor="w",
            wraplength=420,
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(8, 0))

        # Date
        date_str = _date_fr(getattr(g, "date", None))
        coeff    = getattr(g, "coefficient", None)
        meta     = f"Le {date_str}"
        if coeff is not None:
            meta += f"  •  coeff. {coeff}"
        ctk.CTkLabel(
            card,
            text=meta,
            font=ctk.CTkFont(size=10),
            text_color=C["subtext"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=4, pady=(0, 8))

        return card

    def _clear_cards(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

    def _show_info(self, msg: str, *, error: bool = False) -> None:
        self._clear_cards()
        ctk.CTkLabel(
            self._scroll,
            text=msg,
            font=ctk.CTkFont(size=13),
            text_color=C["danger"] if error else C["subtext"],
            wraplength=500,
        ).grid(row=0, column=0, pady=40, padx=20)
