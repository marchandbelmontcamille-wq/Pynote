"""
Persistance du token de session Pronote (ClientMobile).
Stocke URL + username + token dans %APPDATA%/Pynote/session.json
Le token se renouvelle automatiquement à chaque connexion.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pynote.session_store")

# Dossier de stockage : %APPDATA%/Pynote sur Windows, ~/.config/Pynote sinon
_APP_DIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "Pynote"
_SESSION_FILE = _APP_DIR / "session.json"


def save_session(url: str, username: str, token: str) -> None:
    """Sauvegarde l'URL, le nom d'utilisateur et le token dans le fichier de session."""
    _APP_DIR.mkdir(parents=True, exist_ok=True)
    data = {"url": url, "username": username, "token": token}
    _SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.debug("Session sauvegardée dans %s", _SESSION_FILE)


def load_session() -> Optional[dict]:
    """
    Charge la session sauvegardée.
    Retourne un dict {url, username, token} ou None si inexistant.
    """
    if not _SESSION_FILE.exists():
        return None
    try:
        data = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
        if all(k in data for k in ("url", "username", "token")):
            logger.debug("Session chargée depuis %s", _SESSION_FILE)
            return data
    except Exception as exc:
        logger.warning("Impossible de lire la session : %s", exc)
    return None


def clear_session() -> None:
    """Supprime le fichier de session (déconnexion définitive)."""
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()
        logger.info("Session supprimée.")
