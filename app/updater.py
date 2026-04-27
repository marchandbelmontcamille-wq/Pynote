"""
Module d'auto-update pour Pynote.
Vérifie les nouvelles releases sur GitHub et propose le téléchargement.
Fonctionne uniquement dans le bundle PyInstaller (pas en mode script).
Respecte la préférence allow_prerelease de prefs.json.
"""

import sys
import os
import threading
import subprocess
import tempfile
import logging
import urllib.request
import json

import customtkinter as ctk
import config

_PREFS_FILE = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "Pynote", "prefs.json"
)


def _load_prefs() -> dict:
    try:
        with open(_PREFS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

logger = logging.getLogger("pynote.updater")

GITHUB_API        = "https://api.github.com/repos/marchandbelmontcamille-wq/Pynote/releases"
GITHUB_API_LATEST = "https://api.github.com/repos/marchandbelmontcamille-wq/Pynote/releases/latest"
GITHUB_RELEASES   = "https://github.com/marchandbelmontcamille-wq/Pynote/releases/latest"

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


def _parse_version(v: str) -> tuple:
    """Convertit '1.2.3' en (1, 2, 3) pour comparaison."""
    v = v.lstrip("v").strip()
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0, 0, 0)


def _fetch_latest_release(allow_prerelease: bool = False) -> dict | None:
    """
    Interroge l'API GitHub.
    - Si allow_prerelease=False : utilise /releases/latest (stable uniquement)
    - Si allow_prerelease=True  : utilise /releases et prend la plus récente
    Retourne None si aucune release trouvée ou erreur réseau.
    """
    headers = {"User-Agent": f"Pynote/{config.APP_VERSION}"}
    try:
        if allow_prerelease:
            # Récupérer toutes les releases et prendre la plus récente (index 0)
            req = urllib.request.Request(GITHUB_API + "?per_page=5", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                releases = json.loads(resp.read().decode())
            return releases[0] if releases else None
        else:
            # /releases/latest = première release stable uniquement
            req = urllib.request.Request(GITHUB_API_LATEST, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # Aucune release stable publiée
            logger.info("Aucune release stable disponible (404)")
            return None
        logger.warning("Impossible de vérifier les mises à jour : %s", exc)
        return None
    except Exception as exc:
        logger.warning("Impossible de vérifier les mises à jour : %s", exc)
        return None


def check_for_updates(root: ctk.CTk, *, silent: bool = True) -> None:
    """
    Lance la vérification en arrière-plan.
    Si silent=True, n'affiche rien s'il n'y a pas de mise à jour.
    Si silent=False (bouton Manuel), affiche un message même si à jour.
    """
    # Ne pas vérifier en mode script local
    if not hasattr(sys, "_MEIPASS") and not os.path.exists("build_type.txt"):
        if not silent:
            root.after(0, lambda: _show_up_to_date(root, "(mode dev local, pas de vérification)"))
        return

    threading.Thread(
        target=_check_thread,
        args=(root, silent),
        daemon=True,
    ).start()


def _check_thread(root: ctk.CTk, silent: bool) -> None:
    # Lire la préférence allow_prerelease depuis prefs.json
    prefs     = _load_prefs()
    allow_pre = prefs.get("allow_prerelease", False)

    data = _fetch_latest_release(allow_prerelease=allow_pre)
    if data is None:
        if not silent:
            root.after(0, lambda: _show_error(root, "Impossible de contacter GitHub.\nVérifiez votre connexion ou désactivez Avast temporairement."))
        return

    latest_tag  = data.get("tag_name", "").lstrip("v")
    current_ver = config.APP_VERSION.strip()

    if _parse_version(latest_tag) > _parse_version(current_ver):
        # Trouver l'asset installateur Windows
        assets = data.get("assets", [])
        installer_url  = None
        installer_name = None
        for a in assets:
            name = a.get("name", "")
            if name.endswith(".exe"):
                installer_url  = a.get("browser_download_url")
                installer_name = name
                break

        root.after(0, lambda: _show_update_dialog(
            root, current_ver, latest_tag,
            installer_url, installer_name,
            data.get("body", ""),
        ))
    else:
        if not silent:
            root.after(0, lambda: _show_up_to_date(root, current_ver))


# ------------------------------------------------------------------
# Dialogs
# ------------------------------------------------------------------

class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, master, current: str, latest: str,
                 installer_url: str | None, installer_name: str | None,
                 notes: str):
        super().__init__(master)
        self.title("Mise à jour disponible — Pynote")
        self.geometry("520x380")
        self.resizable(True, True)
        self.configure(fg_color=C["card"])
        self.grab_set()

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width()  - 520) // 2
        y = master.winfo_rooty() + (master.winfo_height() - 380) // 2
        self.geometry(f"+{max(0,x)}+{max(0,y)}")

        self._url  = installer_url
        self._name = installer_name
        self._build(current, latest, notes)
        self.after(50, lambda: _bring_to_front(self))

    def _build(self, current, latest, notes) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self,
            text="🎉  Mise à jour disponible !",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C["success"],
        ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            self,
            text=f"Version actuelle : {current}   →   Nouvelle version : {latest}",
            font=ctk.CTkFont(size=11),
            text_color=C["text"],
        ).grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")

        # Notes de release
        box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=10),
            fg_color="#0a0d14",
            text_color=C["subtext"],
            border_width=1,
            border_color=C["border"],
            corner_radius=6,
        )
        box.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="nsew")
        box.insert("1.0", notes or "Aucune note de version disponible.")
        box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=24, pady=(0, 20), sticky="e")

        ctk.CTkButton(
            btn_frame,
            text="Plus tard",
            width=90, height=32,
            font=ctk.CTkFont(size=11),
            fg_color=C["border"],
            hover_color="#3a4060",
            corner_radius=6,
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 8))

        if self._url:
            ctk.CTkButton(
                btn_frame,
                text="⬇️  Télécharger et installer",
                width=190, height=32,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=C["accent"],
                hover_color="#3a6fd8",
                corner_radius=6,
                command=self._download_and_install,
            ).grid(row=0, column=1)
        else:
            ctk.CTkButton(
                btn_frame,
                text="Voir sur GitHub",
                width=140, height=32,
                font=ctk.CTkFont(size=11),
                fg_color=C["accent"],
                hover_color="#3a6fd8",
                corner_radius=6,
                command=lambda: os.startfile(GITHUB_RELEASES),
            ).grid(row=0, column=1)

    def _download_and_install(self) -> None:
        """Télécharge l'installateur et le lance."""
        self._progress_lbl = ctk.CTkLabel(
            self, text="Téléchargement en cours…",
            font=ctk.CTkFont(size=11), text_color=C["warning"],
        )
        self._progress_lbl.grid(row=4, column=0, padx=24, pady=(0, 8))
        threading.Thread(target=self._dl_thread, daemon=True).start()

    def _dl_thread(self) -> None:
        try:
            tmp = tempfile.mktemp(suffix=".exe", prefix="pynote_update_")
            urllib.request.urlretrieve(self._url, tmp)
            self.after(0, lambda: self._launch_installer(tmp))
        except Exception as exc:
            self.after(0, lambda: self._progress_lbl.configure(
                text=f"Erreur : {exc}", text_color=C["danger"]
            ))

    def _launch_installer(self, path: str) -> None:
        try:
            subprocess.Popen([path], shell=True)
            # Fermer Pynote pour laisser l'installateur se lancer
            self.after(500, lambda: sys.exit(0))
        except Exception as exc:
            self._progress_lbl.configure(
                text=f"Impossible de lancer l'installateur : {exc}",
                text_color=C["danger"],
            )


def _bring_to_front(dlg: ctk.CTkToplevel) -> None:
    """Force le dialog au premier plan sur Windows."""
    try:
        dlg.lift()
        dlg.attributes("-topmost", True)
        dlg.after(200, lambda: dlg.attributes("-topmost", False))
        dlg.focus_force()
    except Exception:
        pass


def _show_up_to_date(root: ctk.CTk, version: str) -> None:
    dlg = ctk.CTkToplevel(root)
    dlg.title("Pynote — À jour")
    dlg.geometry("340x130")
    dlg.resizable(False, False)
    dlg.configure(fg_color=C["card"])
    dlg.grab_set()
    x = root.winfo_rootx() + (root.winfo_width()  - 340) // 2
    y = root.winfo_rooty() + (root.winfo_height() - 130) // 2
    dlg.geometry(f"+{max(0,x)}+{max(0,y)}")
    dlg.after(50, lambda: _bring_to_front(dlg))
    ctk.CTkLabel(
        dlg, text=f"✅  Pynote {version} est à jour.",
        font=ctk.CTkFont(size=12), text_color=C["success"],
    ).pack(pady=(24, 8))
    ctk.CTkButton(
        dlg, text="OK", width=80, height=30,
        fg_color=C["accent"], hover_color="#3a6fd8",
        command=dlg.destroy,
    ).pack()


def _show_error(root: ctk.CTk, msg: str) -> None:
    dlg = ctk.CTkToplevel(root)
    dlg.title("Pynote — Erreur")
    dlg.geometry("360x130")
    dlg.resizable(False, False)
    dlg.configure(fg_color=C["card"])
    dlg.grab_set()
    x = root.winfo_rootx() + (root.winfo_width()  - 360) // 2
    y = root.winfo_rooty() + (root.winfo_height() - 130) // 2
    dlg.geometry(f"+{max(0,x)}+{max(0,y)}")
    dlg.after(50, lambda: _bring_to_front(dlg))
    ctk.CTkLabel(
        dlg, text=f"❌  {msg}",
        font=ctk.CTkFont(size=12), text_color=C["danger"], wraplength=300,
    ).pack(pady=(24, 8))
    ctk.CTkButton(
        dlg, text="OK", width=80, height=30,
        fg_color=C["accent"], hover_color="#3a6fd8",
        command=dlg.destroy,
    ).pack()
