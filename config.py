"""
Configuration de l'application Pynote.
Charge les variables d'environnement selon APP_ENV (dev / prod).
"""

import os
import logging
from dotenv import load_dotenv

# Charge .env si présent (mode dev uniquement)
load_dotenv()

# Priorité : variable d'env > fichier build_type.txt (injecté par CI) > prod
APP_ENV: str = os.getenv("APP_ENV", "").lower()
if not APP_ENV:
    try:
        import sys
        _base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        _bt = os.path.join(_base, "build_type.txt")
        if os.path.exists(_bt):
            APP_ENV = open(_bt).read().strip().lower()
    except Exception:
        pass
if not APP_ENV:
    APP_ENV = "prod"

IS_DEV: bool = APP_ENV == "dev"

# Logging
LOG_LEVEL = logging.DEBUG if IS_DEV else logging.WARNING
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("pynote.config")
logger.debug("Mode : %s", APP_ENV.upper())

# Credentials (disponibles uniquement en mode dev via .env)
PRONOTE_URL: str = os.getenv("PRONOTE_URL", "")
PRONOTE_USER: str = os.getenv("PRONOTE_USER", "")
PRONOTE_PASS: str = os.getenv("PRONOTE_PASS", "")
