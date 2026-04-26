"""
Configuration de l'application Pynote.
Charge les variables d'environnement selon APP_ENV (dev / prod).
"""

import os
import logging
from dotenv import load_dotenv

# Charge .env si présent (mode dev uniquement)
load_dotenv()

APP_ENV: str = os.getenv("APP_ENV", "prod").lower()
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
