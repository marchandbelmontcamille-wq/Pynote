"""
Service de connexion et de récupération des données Pronote.
Utilise la bibliothèque pronotepy.
"""

import logging
from datetime import date, timedelta
from typing import Optional

import pronotepy

logger = logging.getLogger("pynote.service")


class PronoteService:
    """Encapsule la connexion et les appels à l'API Pronote."""

    def __init__(self) -> None:
        self._client: Optional[pronotepy.Client] = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.logged_in

    def connect(self, url: str, username: str, password: str) -> None:
        """
        Établit la connexion à Pronote.

        :param url: URL de la page élève (ex: https://xxx/pronote/eleve.html)
        :param username: Identifiant Pronote
        :param password: Mot de passe Pronote
        :raises ConnectionError: En cas d'échec de connexion
        """
        logger.debug("Tentative de connexion à %s avec l'utilisateur %s", url, username)
        try:
            self._client = pronotepy.Client(url, username=username, password=password)
            if not self._client.logged_in:
                raise ConnectionError("Identifiants incorrects ou serveur inaccessible.")
            logger.info("Connexion réussie pour %s", username)
        except Exception as exc:
            self._client = None
            logger.error("Échec de connexion : %s", exc)
            raise ConnectionError(str(exc)) from exc

    def disconnect(self) -> None:
        """Déconnecte le client Pronote."""
        self._client = None
        logger.info("Déconnexion effectuée.")

    def get_timetable(self, target_date: Optional[date] = None) -> list:
        """
        Retourne la liste des cours de la semaine contenant target_date.

        :param target_date: Date de référence (défaut : aujourd'hui)
        :return: Liste de pronotepy.Lesson triée par date/heure
        :raises RuntimeError: Si non connecté
        """
        self._require_connected()
        if target_date is None:
            target_date = date.today()

        # Calculer lundi et dimanche de la semaine
        monday = target_date - timedelta(days=target_date.weekday())
        sunday = monday + timedelta(days=6)

        logger.debug("Récupération EDT du %s au %s", monday, sunday)
        try:
            lessons = self._client.lessons(monday, sunday)
            return sorted(lessons, key=lambda l: l.start)
        except Exception as exc:
            logger.error("Erreur récupération EDT : %s", exc)
            raise RuntimeError(f"Impossible de récupérer l'emploi du temps : {exc}") from exc

    def get_homework(self, until: Optional[date] = None) -> list:
        """
        Retourne les devoirs à rendre entre aujourd'hui et `until`.

        :param until: Date limite (défaut : dans 14 jours)
        :return: Liste de pronotepy.Homework triée par échéance
        :raises RuntimeError: Si non connecté
        """
        self._require_connected()
        today = date.today()
        if until is None:
            until = today + timedelta(days=14)

        logger.debug("Récupération devoirs du %s au %s", today, until)
        try:
            homework_list = self._client.homework(today, until)
            return sorted(homework_list, key=lambda h: h.date)
        except Exception as exc:
            logger.error("Erreur récupération devoirs : %s", exc)
            raise RuntimeError(f"Impossible de récupérer les devoirs : {exc}") from exc

    # ------------------------------------------------------------------
    # Helpers privés
    # ------------------------------------------------------------------

    def _require_connected(self) -> None:
        if not self.is_connected:
            raise RuntimeError("Non connecté à Pronote. Veuillez vous connecter d'abord.")
