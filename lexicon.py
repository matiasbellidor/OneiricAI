"""Fitbit Web API source — structured skeleton, first real integration on the roadmap.

Why Fitbit first: it is the only major wearable with a plain OAuth2 + REST API
(no native app required). A "Personal" app type grants intraday heart-rate
access for the account owner — exactly what a solo-founder MVP needs.

To enable:
  1. Register an app at https://dev.fitbit.com/apps (type: Personal).
  2. Set FITBIT_CLIENT_ID / FITBIT_CLIENT_SECRET / FITBIT_REDIRECT_URI env vars.
  3. Implement the two TODOs below (token exchange + night fetch) and map the
     responses into the shared SleepSession model.

Relevant endpoints:
  - Authorize: https://www.fitbit.com/oauth2/authorize
  - Token:     https://api.fitbit.com/oauth2/token
  - Sleep log: GET /1.2/user/-/sleep/date/{date}.json          (stages incl. REM)
  - Intraday:  GET /1/user/-/activities/heart/date/{date}/1d/1min.json
"""

from __future__ import annotations

import os
from urllib.parse import urlencode

from ...models import SleepSession

AUTHORIZE_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"
SCOPES = "sleep heartrate"


class FitbitSource:
    name = "fitbit"

    def __init__(self) -> None:
        self.client_id = os.getenv("FITBIT_CLIENT_ID", "")
        self.client_secret = os.getenv("FITBIT_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("FITBIT_REDIRECT_URI", "")

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    def auth_url(self, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
        return f"{AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        # TODO: POST TOKEN_URL with Basic auth (client_id:client_secret) and
        # grant_type=authorization_code; persist access/refresh tokens per user.
        raise NotImplementedError("Fitbit token exchange: wire when credentials are set.")

    def fetch_night(self, user_id: str, night_date: str) -> SleepSession:
        # TODO: GET sleep stages + 1-min intraday HR for `night_date`, resample
        # to 5-min epochs, and return a SleepSession (see synthetic.py for shape).
        raise NotImplementedError("Fitbit fetch: wire when credentials are set.")
