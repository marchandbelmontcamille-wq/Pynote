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

_MAX_RETRY   = 2
_RETRY_DELAY = 1.5


def _is_session_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("session", "token", "expired", "login", "authentif"))


def _call_with_retry(fn, *args, **kwargs):
    last_exc: Exception = RuntimeError("Aucune tentative effectuée")
    for attempt in range(1, _MAX_RETRY + 2):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if _is_session_error(exc):
                raise
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
    # Connexion initiale
    # ------------------------------------------------------------------

    def connect(self, url: str, username: str, password: str) -> None:
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
            logger.info("Connexion réussie (UUID: %s)", device_uuid)
        except Exception as exc:
            self._client = None
            msg = exc.args[0] if exc.args else str(exc)
            if isinstance(msg, tuple):
                msg = msg[0]
            logger.error("Échec connexion : %s", msg)
            raise ConnectionError(str(msg)) from exc

    # ------------------------------------------------------------------
    # Reconnexion via token
    # ------------------------------------------------------------------

    def reconnect_from_token(self) -> bool:
        session = load_session()
        if not session:
            return False
        creds = session.get("creds", {})
        if not creds or not creds.get("client_identifier") or not creds.get("uuid"):
            clear_session()
            return False
        try:
            self._client = _call_with_retry(
                pronotepy.Client.token_login,
                pronote_url=creds["pronote_url"],
                username=creds["username"],
                password=creds["password"],
                uuid=creds["uuid"],
                client_identifier=creds["client_identifier"],
            )
            if not self._client.logged_in:
                clear_session()
                return False
            new_creds = self._client.export_credentials()
            new_creds["uuid"] = creds["uuid"]
            save_session(creds["pronote_url"], creds["username"], new_creds)
            return True
        except Exception as exc:
            logger.warning("Reconnexion via token échouée : %s", exc)
            clear_session()
            self._client = None
            return False

    def _auto_reconnect(self) -> bool:
        return self.reconnect_from_token()

    # ------------------------------------------------------------------
    # Déconnexion
    # ------------------------------------------------------------------

    def disconnect(self) -> None:
        self._client = None
        clear_session()

    # ------------------------------------------------------------------
    # Périodes
    # ------------------------------------------------------------------

    def get_periods(self) -> list:
        """Retourne la liste de toutes les Period disponibles."""
        self._ensure_connected()
        try:
            return list(self._client.periods)
        except Exception as exc:
            raise RuntimeError(f"Impossible de récupérer les périodes : {exc}") from exc

    def get_current_period(self) -> Optional[pronotepy.Period]:
        """Retourne la période courante (current_period) ou None."""
        self._ensure_connected()
        try:
            return self._client.current_period
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Données (basées sur une Period explicite)
    # ------------------------------------------------------------------

    def get_timetable(self, target_date: Optional[date] = None) -> list:
        self._ensure_connected()
        if target_date is None:
            target_date = date.today()
        monday = target_date - timedelta(days=target_date.weekday())
        sunday  = monday + timedelta(days=6)
        return self._safe_call(
            lambda: sorted(self._client.lessons(monday, sunday), key=lambda l: l.start),
            "Impossible de récupérer l'emploi du temps",
        )

    def get_homework(self, until: Optional[date] = None) -> list:
        self._ensure_connected()
        today = date.today()
        if until is None:
            until = today + timedelta(days=14)
        return self._safe_call(
            lambda: sorted(self._client.homework(today, until), key=lambda h: h.date),
            "Impossible de récupérer les devoirs",
        )

    def get_grades(self, period: Optional[pronotepy.Period] = None) -> list:
        """Notes d'une période. Utilise current_period si non précisé."""
        self._ensure_connected()
        p = period or self._client.current_period
        return self._safe_call(
            lambda: list(p.grades),
            "Impossible de récupérer les notes",
        )

    def get_averages(self, period: Optional[pronotepy.Period] = None) -> list:
        """Moyennes par matière (Average) d'une période."""
        self._ensure_connected()
        p = period or self._client.current_period
        return self._safe_call(
            lambda: list(p.averages),
            "Impossible de récupérer les moyennes",
        )

    def get_overall_average(self, period: Optional[pronotepy.Period] = None) -> Optional[str]:
        """Moyenne générale de l'élève calculée par l'établissement."""
        self._ensure_connected()
        p = period or self._client.current_period
        return self._safe_call(
            lambda: getattr(p, "overall_average", None),
            "Impossible de récupérer la moyenne générale",
        )

    def get_class_overall_average(self, period: Optional[pronotepy.Period] = None) -> Optional[str]:
        """Moyenne générale de la classe."""
        self._ensure_connected()
        p = period or self._client.current_period
        return self._safe_call(
            lambda: getattr(p, "class_overall_average", None),
            "Impossible de récupérer la moyenne classe",
        )

    def get_absences(self, period: Optional[pronotepy.Period] = None) -> list:
        self._ensure_connected()
        p = period or self._client.current_period
        return self._safe_call(
            lambda: list(p.absences),
            "Impossible de récupérer les absences",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> None:
        if not self.is_connected:
            raise RuntimeError("Non connecté à Pronote.")

    def _safe_call(self, fn, error_prefix: str):
        try:
            return _call_with_retry(fn)
        except Exception as exc:
            if _is_session_error(exc):
                if self._auto_reconnect():
                    try:
                        return _call_with_retry(fn)
                    except Exception as exc2:
                        raise RuntimeError(f"{error_prefix} : {exc2}") from exc2
                else:
                    raise RuntimeError("Session expirée — veuillez vous reconnecter.") from exc
            raise RuntimeError(f"{error_prefix} : {exc}") from exc
