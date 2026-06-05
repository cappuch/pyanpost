from __future__ import annotations

from typing import Any

import httpx

from anpost.exceptions import AnPostHTTPError, AnPostParseError
from anpost.models import (
    ItemSummary,
    MailType,
    PostalRateResult,
    TrackingEvent,
    TrackingResult,
)

_DEFAULT_SUBSCRIPTION_KEY = "01b0162771e941639046a97936f72e95"
_DEFAULT_RATES_SUBSCRIPTION_KEY = "40d54cd8306f42e890831ef7b46bb4f5"
_RATES_BASE = "https://apim-anpost-apwebapis.anpost.com/apweb-intservicesapi"

_DEFAULT_HEADERS: dict[str, str] = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://www.anpost.com",
    "referer": "https://www.anpost.com/",
    "user-agent": "Mozilla/5.0",
}


class AnPostTracker:
    def __init__(
        self,
        subscription_key: str | None = None,
        timeout: float = 20.0,
        base_url: str = "https://apim-anpost-apwebapis.anpost.com/ttservice-public-apweb",
        rates_subscription_key: str | None = None,
        customer_id: str | None = None,
        session_id: str | None = None,
        jwt: str | None = None,
        bearer_token: str | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            headers={
                **_DEFAULT_HEADERS,
                "ocp-apim-subscription-key": subscription_key or _DEFAULT_SUBSCRIPTION_KEY,
            },
            timeout=httpx.Timeout(timeout),
        )
        self._rates_subscription_key = rates_subscription_key or _DEFAULT_RATES_SUBSCRIPTION_KEY
        self._customer_id = customer_id
        self._session_id = session_id
        self._jwt = jwt
        self._bearer_token = bearer_token

    def get_events(self, tracking_number: str) -> list[TrackingEvent]:
        data = self._post("/GetEvents", {"getEvents": {"barcodeItem": tracking_number}})
        result = _navigate(data, "getEventsResponse", "GetEventsResult")
        if result is None:
            return []
        if not isinstance(result, list):
            return []
        return [TrackingEvent.from_api(item) for item in result]

    def is_delivered(self, tracking_number: str) -> bool:
        data = self._post(
            "/CheckStatusDelivered",
            {"checkStatusDelivered": {"barcodeItem": tracking_number}},
        )
        result = _navigate(data, "checkStatusDeliveredResponse", "checkStatusDeliveredResult")
        if result is None:
            return False
        return bool(result)

    def get_item_summary(self, tracking_number: str) -> list[ItemSummary]:
        data = self._post(
            "/GetItemSummary",
            {"getItemSummary": {"trackingItems": [tracking_number]}},
        )
        result = _navigate(data, "getItemSummaryResponse", "GetItemSummaryResult")
        if result is None:
            return []
        if not isinstance(result, list):
            return []
        return [ItemSummary.from_api(item) for item in result]

    def track(self, tracking_number: str) -> TrackingResult:
        events = self.get_events(tracking_number)
        summary = self.get_item_summary(tracking_number)
        delivered = self.is_delivered(tracking_number)
        return TrackingResult(
            tracking_number=tracking_number,
            delivered=delivered,
            events=events,
            summary=summary,
        )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._client.post(url, json=payload)
        except httpx.RequestError as exc:
            raise AnPostHTTPError(0, str(exc)) from exc

        if not response.is_success:
            raise AnPostHTTPError(response.status_code, response.text)

        try:
            return response.json()
        except ValueError as exc:
            raise AnPostParseError(f"Invalid JSON response: {exc}") from exc

    def get_rates(
        self,
        country_code: str,
        weight: float,
        mail_type: MailType | str,
        goods: bool = True,
    ) -> PostalRateResult:
        params: dict[str, str | float] = {
            "countryCode": country_code,
            "weight": weight,
            "mailType": mail_type.value if isinstance(mail_type, MailType) else mail_type,
            "goods": "true" if goods else "false",
        }
        headers: dict[str, str] = {
            **_DEFAULT_HEADERS,
            "accept": "application/json, text/plain, */*",
            "ocp-apim-subscription-key": self._rates_subscription_key,
        }
        if self._customer_id:
            headers["anp-cp-clickpostbasketciamcustomerid"] = self._customer_id
        if self._session_id:
            headers["anp-cp-sessionid"] = self._session_id
        if self._jwt:
            headers["anp-cp-jwt"] = self._jwt
        if self._bearer_token:
            headers["authorization"] = f"Bearer {self._bearer_token}"

        data = self._get("/v1/clickpost/rates", params=params, headers=headers, base=_RATES_BASE)
        return PostalRateResult.from_api(data)

    def close(self) -> None:
        self._client.close()


    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        base: str | None = None,
    ) -> dict[str, Any]:
        url = f"{base or self._base_url}{path}"
        request_headers = self._client.headers.copy()
        if headers:
            request_headers.update(headers)
        try:
            response = self._client.get(url, params=params, headers=request_headers)
        except httpx.RequestError as exc:
            raise AnPostHTTPError(0, str(exc)) from exc

        if not response.is_success:
            raise AnPostHTTPError(response.status_code, response.text)

        try:
            return response.json()
        except ValueError as exc:
            raise AnPostParseError(f"Invalid JSON response: {exc}") from exc


def _navigate(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
