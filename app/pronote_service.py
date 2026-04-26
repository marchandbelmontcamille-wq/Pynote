"""
Service de connexion Pronote.
Utilise export_credentials() + token_login() + UUID stable pour persister la session.
"""

import logging
import uuid as _uuid_mod
from datetime import date, timedelta
from typing import Optional

import pronotepy

from app.session_store import save_session, load_session, clear_session

logger = logging.getLogger("pynote.service")


class PronoteService:
    """Encapsule la connexion et les appels à l'API Pronote."""

    def __init__(self) -> None:
        self._client: Optional[pronotepy.Client] = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.logged_in

    # ------------------------------------------------------------------
    # Connexion initiale (identifiant + mot de passe)
    # ------------------------------------------------------------------

    def connect(self, url: str, username: str, password: str) -> None:
        """
        Connexion initiale avec identifiant + mot de passe.
        Génère un UUID device stable et sauvegarde les credentials.

        :raises ConnectionError: En cas d'échec
        """
        logger.debug("Connexion à %s (utilisateur: %s)", url, username)

        # Récupérer l'UUID existant ou en créer un nouveau
        session = load_session()
        device_uuid = session.get("uuid", "") if session else ""
        if not device_uuid:
            device_uuid = str(_uuid_mod.uuid4())

        try:
            self._client = pronotepy.Client(
                url,
                username=username,
                password=password,
                uuid=device_uuid,
            )
            if not self._client.logged_in:
                raise ConnectionError("Identifiants incorrects ou serveur inaccessible.")

            creds = self._client.export_credentials()
            creds["uuid"] = device_uuid
            save_session(url, username, creds)
            logger.info("Connexion réussie — credentials sauvegardés (UUID: %s)", device_uuid)

        except Exception as exc:
            self._client = None
            msg = exc.args[0] if exc.args else str(exc)
            if isinstance(msg, tuple):
                msg = msg[0]
            logger.error("Échec connexion : %s", msg)
            raise ConnectionError(str(msg)) from exc

    # ------------------------------------------------------------------
    # Reconnexion via token (token_login)
    # ------------------------------------------------------------------

    def reconnect_from_token(self) -> bool:
        """
        Tente de restaurer la session via token_login() sans ressaisir le mot de passe.

        :returns: True si succès, False si le token est absent/expiré
        """
        session = load_session()
        if not session:
            logger.debug("Aucune session sauvegardée.")
            return False

        creds = session.get("creds", {})
        if not creds or not creds.get("client_identifier") or not creds.get("uuid"):
            logger.debug("Credentials incomplets pour token_login.")
            clear_session()
            return False

        try:
            logger.debug("Reconnexion via token pour %s", creds.get("username"))
            self._client = pronotepy.Client.token_login(
                pronote_url=creds["pronote_url"],
                username=creds["username"],
                password=creds["password"],
                uuid=creds["uuid"],
                client_identifier=creds["client_identifier"],
            )
            if not self._client.logged_in:
                logger.warning("Token expiré ou invalide.")
                clear_session()
                return False

            # Renouveler les credentials
            new_creds = self._client.export_credentials()
            new_creds["uuid"] = creds["uuid"]
            save_session(creds["pronote_url"], creds["username"], new_creds)
            logger.info("Reconnexion via token réussie pour %s.", creds.get("username"))
            return True

        except Exception as exc:
            logger.warning("Reconnexion via token échouée : %s", exc)
            clear_session()
            self._client = None
            return False

    # ------------------------------------------------------------------
    # Déconnexion
    # ------------------------------------------------------------------

    def disconnect(self) -> None:
        """Déconnecte et supprime les credentials sauvegardés."""
        self._client = None
        clear_session()
        logger.info("Déconnexion + suppression des credentials.")

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def get_timetable(self, target_date: Optional[date] = None) -> list:
        """Retourne les cours de la semaine contenant target_date."""
        self._ensure_connected()
        if target_date is None:
            target_date = date.today()
        monday = target_date - timedelta(days=target_date.weekday())
        sunday = monday + timedelta(days=6)
        logger.debug("EDT du %s au %s", monday, sunday)
        try:
            return sorted(self._client.lessons(monday, sunday), key=lambda l: l.start)
        except Exception as exc:
            raise RuntimeError(f"Impossible de récupérer l'emploi du temps : {exc}") from exc

    def get_homework(self, until: Optional[date] = None) -> list:
        """Retourne les devoirs entre aujourd'hui et `until`."""
        self._ensure_connected()
        today = date.today()
        if until is None:
            until = today + timedelta(days=14)
        logger.debug("Devoirs du %s au %s", today, until)
        try:
            return sorted(self._client.homework(today, until), key=lambda h: h.date)
        except Exception as exc:
            raise RuntimeError(f"Impossible de récupérer les devoirs : {exc}") from exc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> None:
        if not self.is_connected:
            raise RuntimeError("Non connecté à Pronote.")
