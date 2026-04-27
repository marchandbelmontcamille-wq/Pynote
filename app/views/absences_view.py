"""
Vue Absences — affiche les absences et retards du trimestre courant.
"""

import threading
import logging
import customtkinter as ctk

from app.pronote_service import PronoteService

logger = logging.getLogger("pynote.absences")

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


class AbsencesView(ctk.CTkFrame):
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
            text="🚫  Absences & Retards",
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

        self._show_info("Cliquez sur ↻ Actualiser pour charger les absences.")

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        self._clear_cards()
        self._show_info("Chargement…")
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self) -> None:
        try:
            absences = self._service.get_absences()
            self.after(0, self._display_absences, absences)
        except Exception as exc:
            self.after(0, self._show_info, f"Erreur : {exc}", True)

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------

    def _display_absences(self, absences: list) -> None:
        self._clear_cards()
        if not absences:
            self._show_info("✅  Aucune absence enregistrée pour ce trimestre.")
            return

        # Compteurs résumé
        nb_abs    = sum(1 for a in absences if not getattr(a, "is_delay", False))
        nb_retard = sum(1 for a in absences if getattr(a, "is_delay", False))
        summary = f"{len(absences)} entrée(s)  •  {nb_abs} absence(s)  •  {nb_retard} retard(s)"
        ctk.CTkLabel(
            self._scroll,
            text=summary,
            font=ctk.CTkFont(size=11),
            text_color=C["subtext"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(12, 6))

        for idx, a in enumerate(absences):
            card = self._make_absence_card(a)
            card.grid(row=idx + 1, column=0, sticky="ew", padx=16, pady=3)

    def _make_absence_card(self, a) -> ctk.CTkFrame:
        is_delay = getattr(a, "is_delay", False)
        justified = getattr(a, "justified", False)

        # Couleur de la puce selon type
        if is_delay:
            badge_color = C["warning"]
            badge_text  = "RETARD"
        elif justified:
            badge_color = C["success"]
            badge_text  = "JUSTIFIÉE"
        else:
            badge_color = C["danger"]
            badge_text  = "ABSENCE"

        card = ctk.CTkFrame(
            self._scroll,
            fg_color=C["card"],
            corner_radius=8,
            border_width=1,
            border_color=C["border"],
        )
        card.grid_columnconfigure(1, weight=1)

        # Badge type
        ctk.CTkLabel(
            card,
            text=badge_text,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#0f1117",
            fg_color=badge_color,
            corner_radius=4,
            width=72,
            height=22,
        ).grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10)

        # Dates
        from_dt = getattr(a, "from_date", None) or getattr(a, "start", None)
        to_dt   = getattr(a, "to_date",   None) or getattr(a, "end",   None)
        if from_dt and to_dt and _date_fr(from_dt) != _date_fr(to_dt):
            date_txt = f"Du {_date_fr(from_dt)} au {_date_fr(to_dt)}"
        elif from_dt:
            date_txt = f"Le {_date_fr(from_dt)}"
        else:
            date_txt = "Date inconnue"

        ctk.CTkLabel(
            card,
            text=date_txt,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(10, 0))

        # Raison / durée
        reason   = getattr(a, "reason",    "") or ""
        duration = getattr(a, "duration",  None)
        meta_parts = []
        if duration is not None:
            try:
                h = int(duration.total_seconds() // 3600)
                m = int((duration.total_seconds() % 3600) // 60)
                meta_parts.append(f"{h}h{m:02d}" if h else f"{m} min")
            except Exception:
                pass
        if reason:
            meta_parts.append(reason)
        meta = "  •  ".join(meta_parts) if meta_parts else "—"

        ctk.CTkLabel(
            card,
            text=meta,
            font=ctk.CTkFont(size=10),
            text_color=C["subtext"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=4, pady=(0, 10))

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
