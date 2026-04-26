"""
Service de connexion Pronote via ClientMobile.
Utilise un token persisté pour éviter les reconnexions répétées.
"""

import logging
from datetime import date, timedelta
from typing import Optional

import pronotepy

from app.session_store import save_session, load_session, clear_session

logger = logging.getLogger("pynote.service")


class PronoteService:
    """Encapsule la connexion et les appels à l'API Pronote (ClientMobile)."""

    def __init__(self) -> None:
        self._client: Optional[pronotepy.ClientMobile] = None
        self._url: str = ""
        self._username: str = ""

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.logged_in

    # ------------------------------------------------------------------
    # Connexion
    # ------------------------------------------------------------------

    def connect(self, url: str, username: str, password: str) -> None:
        """
        Connexion initiale avec identifiant + mot de passe.
        Sauvegarde le token pour les prochaines connexions.

        :raises ConnectionError: En cas d'échec
        """
        logger.debug("Connexion à %s avec identifiant %s", url, username)
        try:
            self._client = pronotepy.ClientMobile(
                url, username=username, password=password
            )
            if not self._client.logged_in:
                raise ConnectionError("Identifiants incorrects ou serveur inaccessible.")
            self._url = url
            self._username = username
            save_session(url, username, self._client.token)
            logger.info("Connexion réussie — token sauvegardé.")
        except Exception as exc:
            self._client = None
            msg = exc.args[0] if exc.args else str(exc)
            if isinstance(msg, tuple):
                msg = msg[0]
            logger.error("Échec connexion : %s", msg)
            raise ConnectionError(str(msg)) from exc

    def reconnect_from_token(self) -> bool:
        """
        Tente de restaurer la session depuis le token sauvegardé.

        :returns: True si succès, False sinon
        """
        session = load_session()
        if not session:
            return False
        try:
            logger.debug("Tentative de reconnexion via token pour %s", session["username"])
            self._client = pronotepy.ClientMobile(
                session["url"],
                username=session["username"],
                token=session["token"],
            )
            if not self._client.logged_in:
                logger.warning("Token expiré ou invalide.")
                clear_session()
                return False
            self._url = session["url"]
            self._username = session["username"]
            # Renouveler le token
            save_session(self._url, self._username, self._client.token)
            logger.info("Reconnexion via token réussie pour %s.", self._username)
            return True
        except Exception as exc:
            logger.warning("Reconnexion via token échouée : %s", exc)
            clear_session()
            self._client = None
            return False

    def disconnect(self) -> None:
        """Déconnecte et supprime le token sauvegardé."""
        self._client = None
        clear_session()
        logger.info("Déconnexion + suppression du token.")

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def get_timetable(self, target_date: Optional[date] = None) -> list:
        """
        Retourne la liste des cours de la semaine contenant target_date.

        :raises RuntimeError: Si non connecté
        """
        self._ensure_connected()
        if target_date is None:
            target_date = date.today()
        monday = target_date - timedelta(days=target_date.weekday())
        sunday = monday + timedelta(days=6)
        logger.debug("EDT du %s au %s", monday, sunday)
        try:
            lessons = self._client.lessons(monday, sunday)
            return sorted(lessons, key=lambda l: l.start)
        except Exception as exc:
            raise RuntimeError(f"Impossible de récupérer l'emploi du temps : {exc}") from exc

    def get_homework(self, until: Optional[date] = None) -> list:
        """
        Retourne les devoirs entre aujourd'hui et `until`.

        :raises RuntimeError: Si non connecté
        """
        self._ensure_connected()
        today = date.today()
        if until is None:
            until = today + timedelta(days=14)
        logger.debug("Devoirs du %s au %s", today, until)
        try:
            homework_list = self._client.homework(today, until)
            return sorted(homework_list, key=lambda h: h.date)
        except Exception as exc:
            raise RuntimeError(f"Impossible de récupérer les devoirs : {exc}") from exc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> None:
        if not self.is_connected:
            raise RuntimeError("Non connecté à Pronote.")
