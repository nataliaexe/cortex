"""Cliente Google Calendar.

Autenticacao OAuth2 (Desktop). Na primeira execucao, abre o navegador
para autorizar; depois salva o token e reutiliza.

Escopos minimos: calendar (leitura + escrita).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cortex.utils.logging import get_logger

log = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# caminhos
CORTEX_ROOT = Path.home() / "cortex"
CREDENTIALS_PATH = CORTEX_ROOT / "data" / "google_credentials.json"
TOKEN_PATH = CORTEX_ROOT / "data" / "google_token.json"


class GoogleCalendarNotConfigured(Exception):
    pass


class GoogleCalendarAuthError(Exception):
    pass


@dataclass(slots=True)
class GEvent:
    id: str
    summary: str
    description: str | None
    location: str | None
    start_iso: str
    end_iso: str
    all_day: bool
    raw: dict[str, Any]


class GoogleCalendarClient:
    """Cliente fino sobre a API do Google Calendar."""

    def __init__(self, credentials_path: Path | None = None, token_path: Path | None = None) -> None:
        self.credentials_path = credentials_path or CREDENTIALS_PATH
        self.token_path = token_path or TOKEN_PATH
        self._service = None

    def is_configured(self) -> bool:
        return self.credentials_path.exists()

    def has_token(self) -> bool:
        return self.token_path.exists()

    # ---------- autenticacao ----------

    def _load_credentials(self, allow_interactive: bool = False):
        """Carrega credenciais do token salvo, ou inicia fluxo OAuth."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as e:
            raise GoogleCalendarNotConfigured(
                f"bibliotecas do Google nao instaladas: {e}. "
                f"Rode: pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        if not self.is_configured():
            raise GoogleCalendarNotConfigured(
                f"credenciais nao encontradas em {self.credentials_path}"
            )

        creds = None
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            except Exception as e:
                log.warning("google_token_load_failed", error=str(e))
                creds = None

        # se tem credencial mas esta expirada e tem refresh, renova
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
                return creds
            except Exception as e:
                log.warning("google_token_refresh_failed", error=str(e))
                creds = None

        # se nao tem credencial valida, precisa fluxo interativo
        if not creds or not creds.valid:
            if not allow_interactive:
                raise GoogleCalendarAuthError(
                    "token invalido ou ausente. Rode o fluxo interativo uma vez "
                    "com `cortex calendar auth` ou pela primeira vez chamando com "
                    "allow_interactive=True."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            self._save_token(creds)
            log.info("google_token_saved", path=str(self.token_path))

        return creds

    def _save_token(self, creds) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(creds.to_json(), encoding="utf-8")
        # restringe permissoes do arquivo (contem refresh token)
        try:
            os.chmod(self.token_path, 0o600)
        except Exception:
            pass

    def _get_service(self, allow_interactive: bool = False):
        if self._service is not None:
            return self._service
        try:
            from googleapiclient.discovery import build
        except ImportError as e:
            raise GoogleCalendarNotConfigured(
                f"google-api-python-client nao instalado: {e}"
            )
        creds = self._load_credentials(allow_interactive=allow_interactive)
        self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    # ---------- eventos ----------

    def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        max_results: int = 100,
        calendar_id: str = "primary",
        allow_interactive: bool = False,
    ) -> list[GEvent]:
        service = self._get_service(allow_interactive=allow_interactive)
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        items = events_result.get("items", [])
        return [self._parse_event(item) for item in items]

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        location: str | None = None,
        calendar_id: str = "primary",
        allow_interactive: bool = False,
    ) -> GEvent:
        service = self._get_service(allow_interactive=allow_interactive)
        body: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
        }
        if description:
            body["description"] = description
        if location:
            body["location"] = location

        created = service.events().insert(calendarId=calendar_id, body=body).execute()
        return self._parse_event(created)

    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        allow_interactive: bool = False,
    ) -> bool:
        service = self._get_service(allow_interactive=allow_interactive)
        try:
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return True
        except Exception as e:
            log.error("google_delete_failed", event_id=event_id, error=str(e))
            return False

    @staticmethod
    def _parse_event(item: dict[str, Any]) -> GEvent:
        start = item.get("start", {})
        end = item.get("end", {})
        # pode ser 'dateTime' (com hora) ou 'date' (all day)
        if "dateTime" in start:
            start_iso = start["dateTime"]
            end_iso = end.get("dateTime", start_iso)
            all_day = False
        else:
            start_iso = start.get("date", "")
            end_iso = end.get("date", start_iso)
            all_day = True

        return GEvent(
            id=item.get("id", ""),
            summary=item.get("summary", "(sem titulo)"),
            description=item.get("description"),
            location=item.get("location"),
            start_iso=start_iso,
            end_iso=end_iso,
            all_day=all_day,
            raw=item,
        )
