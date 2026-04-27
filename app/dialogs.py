"""
Dialogs réutilisables pour Pynote (CTkToplevel).
"""

import customtkinter as ctk

C = {
    "bg":      "#0f1117",
    "card":    "#1c2333",
    "border":  "#2a3347",
    "accent":  "#4f8ef7",
    "text":    "#e8eaf0",
    "subtext": "#8892a4",
}


class PeriodTypeDialog(ctk.CTkToplevel):
    """
    Popup modale demandant à l'utilisateur s'il est en trimestre ou semestre.
    Résultat accessible via `.result` ("trimestre" | "semestre" | None si fermée).
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("Système de notation")
        self.geometry("380x200")
        self.resizable(False, False)
        self.configure(fg_color=C["card"])
        self.grab_set()          # modale
        self.focus_force()

        # Centrer par rapport à la fenêtre parente
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width()  - 380) // 2
        y = master.winfo_rooty() + (master.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

        self.result: str | None = None
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            self,
            text="Système de notation",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, columnspan=2, padx=24, pady=(24, 6))

        ctk.CTkLabel(
            self,
            text="Ton établissement utilise-t-il des\ntrimestres ou des semestres ?",
            font=ctk.CTkFont(size=12),
            text_color=C["subtext"],
            justify="center",
        ).grid(row=1, column=0, columnspan=2, padx=24, pady=(0, 20))

        ctk.CTkButton(
            self,
            text="📅  Trimestres",
            width=140, height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C["accent"],
            hover_color="#3a6fd8",
            corner_radius=8,
            command=lambda: self._choose("trimestre"),
        ).grid(row=2, column=0, padx=(24, 8), pady=(0, 24), sticky="e")

        ctk.CTkButton(
            self,
            text="📅  Semestres",
            width=140, height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#5a3ea0",
            hover_color="#3e2a70",
            corner_radius=8,
            command=lambda: self._choose("semestre"),
        ).grid(row=2, column=1, padx=(8, 24), pady=(0, 24), sticky="w")

    def _choose(self, value: str) -> None:
        self.result = value
        self.grab_release()
        self.destroy()

    def _on_close(self) -> None:
        self.result = None
        self.grab_release()
        self.destroy()
