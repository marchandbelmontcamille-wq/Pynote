"""
Module d'auto-update pour Pynote.
Vérifie les nouvelles releases sur GitHub et ouvre la page de téléchargement
dans le navigateur par défaut.
"""

import sys
import os
import threading
import webbrowser
import logging
import urllib.request
import json

import customtkinter as ctk
import config

logger = logging.getLogger("pynote.updater")

GITHUB_API        = "https://api.github.com/repos/marchandbelmontcamille-wq/Pynote/releases"
GITHUB_API_LATEST = "https://api.github.com/repos/marchandbelmontcamille-wq/Pynote/releases/latest"
GITHUB_RELEASES   = "https://github.com/marchandbelmontcamille-wq/Pynote/releases/latest"

C = {
    "card":    "#1c2333",
    "border":  "#2a3347",
    "accent":  "#4f8ef7",
    "text":    "#e8eaf0",
    "subtext": "#8892a4",
    "success": "#3dd68c",
    "warning": "#f5a623",
    "danger":  "#e05252",
}

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


def _parse_version(v: str) -> tuple:
    v = v.lstrip("v").strip()
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0, 0, 0)


def _fetch_latest_release(allow_prerelease: bool = False) -> dict | None:
    headers = {"User-Agent": f"Pynote/{config.APP_VERSION}"}
    try:
        if allow_prerelease:
            req = urllib.request.Request(GITHUB_API + "?per_page=5", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                releases = json.loads(resp.read().decode())
            return releases[0] if releases else None
        else:
            req = urllib.request.Request(GITHUB_API_LATEST, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.info("Aucune release stable disponible (404)")
            return None
        logger.warning("Erreur API GitHub : %s", exc)
        return None
    except Exception as exc:
        logger.warning("Impossible de vérifier les mises à jour : %s", exc)
        return None


def check_for_updates(root: ctk.CTk, *, silent: bool = True) -> None:
    """Lance la vérification en arrière-plan."""
    if not hasattr(sys, "_MEIPASS") and not os.path.exists("build_type.txt"):
        if not silent:
            _show_toast(root, "Mode local — pas de vérification de mise à jour.", error=False)
        return

    threading.Thread(target=_check_thread, args=(root, silent), daemon=True).start()


def _check_thread(root: ctk.CTk, silent: bool) -> None:
    prefs     = _load_prefs()
    allow_pre = prefs.get("allow_prerelease", False)

    data = _fetch_latest_release(allow_prerelease=allow_pre)
    if data is None:
        if not silent:
            root.after(0, lambda: _show_toast(
                root,
                "Impossible de contacter GitHub.\nVérifiez votre connexion internet.",
                error=True,
            ))
        return

    latest_tag  = data.get("tag_name", "").lstrip("v")
    current_ver = config.APP_VERSION.strip()
    release_url = data.get("html_url", GITHUB_RELEASES)

    if _parse_version(latest_tag) > _parse_version(current_ver):
        root.after(0, lambda: _show_update_dialog(root, current_ver, latest_tag, release_url, data.get("body", "")))
    else:
        if not silent:
            root.after(0, lambda: _show_toast(root, f"✅  Pynote {current_ver} est à jour.", error=False))


# ------------------------------------------------------------------
# Dialogs
# ------------------------------------------------------------------

def _bring_to_front(w) -> None:
    try:
        w.lift()
        w.attributes("-topmost", True)
        w.after(200, lambda: w.attributes("-topmost", False))
        w.focus_force()
    except Exception:
        pass


def _show_update_dialog(root: ctk.CTk, current: str, latest: str,
                        release_url: str, notes: str) -> None:
    dlg = ctk.CTkToplevel(root)
    dlg.title("Mise à jour disponible — Pynote")
    dlg.geometry("480x320")
    dlg.resizable(True, True)
    dlg.configure(fg_color=C["card"])
    dlg.grab_set()
    dlg.grid_columnconfigure(0, weight=1)
    dlg.grid_rowconfigure(2, weight=1)

    x = root.winfo_rootx() + (root.winfo_width()  - 480) // 2
    y = root.winfo_rooty() + (root.winfo_height() - 320) // 2
    dlg.geometry(f"+{max(0,x)}+{max(0,y)}")
    dlg.after(50, lambda: _bring_to_front(dlg))

    ctk.CTkLabel(
        dlg,
        text="🎉  Mise à jour disponible !",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=C["success"],
    ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

    ctk.CTkLabel(
        dlg,
        text=f"Version actuelle : {current}   →   Nouvelle version : {latest}",
        font=ctk.CTkFont(size=11),
        text_color=C["text"],
    ).grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")

    # Notes de release
    box = ctk.CTkTextbox(
        dlg,
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

    btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
    btn_frame.grid(row=3, column=0, padx=24, pady=(0, 20), sticky="e")

    ctk.CTkButton(
        btn_frame,
        text="Plus tard",
        width=90, height=32,
        font=ctk.CTkFont(size=11),
        fg_color=C["border"],
        hover_color="#3a4060",
        corner_radius=6,
        command=dlg.destroy,
    ).grid(row=0, column=0, padx=(0, 8))

    ctk.CTkButton(
        btn_frame,
        text="⬇️  Télécharger",
        width=140, height=32,
        font=ctk.CTkFont(size=11, weight="bold"),
        fg_color=C["accent"],
        hover_color="#3a6fd8",
        corner_radius=6,
        command=lambda: (webbrowser.open(release_url), dlg.destroy()),
    ).grid(row=0, column=1)


def _show_toast(root: ctk.CTk, msg: str, *, error: bool = False) -> None:
    """Affiche un petit toast en bas de la fenêtre principale."""
    color = C["danger"] if error else C["success"]
    toast = ctk.CTkLabel(
        root,
        text=msg,
        font=ctk.CTkFont(size=11),
        text_color="#0f1117",
        fg_color=color,
        corner_radius=8,
        wraplength=360,
        padx=16,
        pady=8,
    )
    toast.place(relx=0.5, rely=0.96, anchor="center")
    root.after(3500, toast.destroy)
