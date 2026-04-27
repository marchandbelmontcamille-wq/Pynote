"""
Service de connexion Pronote.
Utilise export_credentials() + token_login() + UUID stable pour persister la session.
Gestion d'erreurs renforcée : retry réseau, reconnexion auto sur session expirée.
"""

import logging
import time
import uuid as _uuid_mod
from datetime import date, timedelta
from typing import Optional

import pronotepy

from app.session_store import save_session, load_session, clear_session

logger = logging.getLogger("pynote.service")

# Nombre de tentatives en cas d'erreur réseau transitoire
_MAX_RETRY = 2
_RETRY_DELAY = 1.5   # secondes


def _is_session_error(exc: Exception) -> bool:
    """Détecte si l'exception indique une session expirée."""
    msg = str(exc).lower()
    return any(k in msg for k in ("session", "token", "expired", "login", "authentif"))


def _call_with_retry(fn, *args, **kwargs):
    """Exécute fn(*args, **kwargs) avec jusqu'à _MAX_RETRY relances sur erreur réseau."""
    last_exc: Exception = RuntimeError("Aucune tentative effectuée")
    for attempt in range(1, _MAX_RETRY + 2):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if _is_session_error(exc):
                raise  # session expirée → pas de retry
            if attempt <= _MAX_RETRY:
                logger.warning("Tentative %d/%d échouée (%s), réessai dans %.1fs…",
                               attempt, _MAX_RETRY + 1, exc, _RETRY_DELAY)
                time.sleep(_RETRY_DELAY)
            else:
                logger.error("Toutes les tentatives ont échoué : %s", exc)
    raise last_exc


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

        session = load_session()
        device_uuid = session.get("uuid", "") if session else ""
        if not device_uuid:
            device_uuid = str(_uuid_mod.uuid4())

        try:
            self._client = _call_with_retry(
                pronotepy.Client, url,
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
            self._client = _call_with_retry(
                pronotepy.Client.token_login,
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
    # Reconnexion auto si session expirée lors d'un appel
    # ------------------------------------------------------------------

    def _auto_reconnect(self) -> bool:
        """Tente une reconnexion silencieuse via token si la session est expirée."""
        logger.info("Tentative de reconnexion automatique…")
        return self.reconnect_from_token()

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
        sunday  = monday + timedelta(days=6)
        logger.debug("EDT du %s au %s", monday, sunday)
        return self._safe_call(
            lambda: sorted(self._client.lessons(monday, sunday), key=lambda l: l.start),
            "Impossible de récupérer l'emploi du temps",
        )

    def get_homework(self, until: Optional[date] = None) -> list:
        """Retourne les devoirs entre aujourd'hui et `until`."""
        self._ensure_connected()
        today = date.today()
        if until is None:
            until = today + timedelta(days=14)
        logger.debug("Devoirs du %s au %s", today, until)
        return self._safe_call(
            lambda: sorted(self._client.homework(today, until), key=lambda h: h.date),
            "Impossible de récupérer les devoirs",
        )

    def get_grades(self) -> list:
        """Retourne la liste des notes du trimestre courant."""
        self._ensure_connected()
        logger.debug("Récupération des notes…")
        return self._safe_call(
            lambda: list(self._client.current_period.grades),
            "Impossible de récupérer les notes",
        )

    def get_absences(self) -> list:
        """Retourne la liste des absences/retards."""
        self._ensure_connected()
        logger.debug("Récupération des absences…")
        return self._safe_call(
            lambda: list(self._client.current_period.absences),
            "Impossible de récupérer les absences",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> None:
        if not self.is_connected:
            raise RuntimeError("Non connecté à Pronote.")

    def _safe_call(self, fn, error_prefix: str):
        """
        Exécute fn() avec retry réseau.
        Si session expirée → tente une reconnexion auto et réessaie une fois.
        """
        try:
            return _call_with_retry(fn)
        except Exception as exc:
            if _is_session_error(exc):
                logger.info("Session expirée, tentative de reconnexion auto…")
                if self._auto_reconnect():
                    try:
                        return _call_with_retry(fn)
                    except Exception as exc2:
                        raise RuntimeError(f"{error_prefix} : {exc2}") from exc2
                else:
                    raise RuntimeError("Session expirée — veuillez vous reconnecter.") from exc
            raise RuntimeError(f"{error_prefix} : {exc}") from exc
