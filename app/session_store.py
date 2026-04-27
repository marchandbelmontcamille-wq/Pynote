"""
Persistance des credentials Pronote (export_credentials + uuid).
Stocke dans %APPDATA%/Pynote/session.json
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pynote.session_store")

_APP_DIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "Pynote"
_SESSION_FILE = _APP_DIR / "session.json"


def save_session(url: str, username: str, creds: dict) -> None:
    """Sauvegarde URL, username et le dict export_credentials."""
    _APP_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "url": url,
        "username": username,
        "creds": creds,
        "uuid": creds.get("uuid", ""),
    }
    _SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.debug("Session sauvegardée dans %s", _SESSION_FILE)


def load_session() -> Optional[dict]:
    """Charge la session sauvegardée. Retourne None si absente/invalide."""
    if not _SESSION_FILE.exists():
        return None
    try:
        data = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
        if "url" in data and "username" in data and "creds" in data:
            logger.debug("Session chargée depuis %s", _SESSION_FILE)
            return data
        else:
            logger.debug("Format de session incompatible — suppression.")
            _SESSION_FILE.unlink(missing_ok=True)
    except Exception as exc:
        logger.warning("Impossible de lire la session : %s", exc)
    return None


def clear_session() -> None:
    """Supprime le fichier de session."""
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()
        logger.info("Session supprimée.")
