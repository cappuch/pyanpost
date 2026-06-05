from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
import pytest

from anpost import AnPostTracker
from anpost.exceptions import AnPostHTTPError, AnPostParseError
from anpost.models import ItemSummary, TrackingEvent, TrackingResult


@pytest.fixture
def tracker() -> AnPostTracker:
    return AnPostTracker()


def test_get_events_success(httpx_mock, tracker: AnPostTracker) -> None:
    payload = {
        "getEventsResponse": {
            "GetEventsResult": [
                {
                    "activity": "Item delivered",
                    "date": "2026-06-04T10:00:00",
                    "location": "Dublin",
                    "reason": "",
                    "traceCode": 99,
                },
            ],
        },
    }
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        json=payload,
    )

    events = tracker.get_events("LABEL")
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, TrackingEvent)
    assert event.activity == "Item delivered"
    assert event.date == datetime(2026, 6, 4, 10, 0, 0)
    assert event.location == "Dublin"
    assert event.trace_code == 99


def test_get_events_empty_result(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        json={"getEventsResponse": {"GetEventsResult": []}},
    )
    assert tracker.get_events("LABEL") == []


def test_get_events_missing_key_returns_empty(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        json={"getEventsResponse": {}},
    )
    assert tracker.get_events("LABEL") == []


def test_get_events_non_list_returns_empty(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        json={"getEventsResponse": {"GetEventsResult": "not_a_list"}},
    )
    assert tracker.get_events("LABEL") == []


def test_get_events_invalid_date_returns_none(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        json={
            "getEventsResponse": {
                "GetEventsResult": [
                    {
                        "activity": "test",
                        "date": "not-a-date",
                        "location": "",
                        "reason": "",
                        "traceCode": None,
                    },
                ],
            },
        },
    )
    events = tracker.get_events("LABEL")
    assert events[0].date is None


def test_get_events_empty_date_returns_none(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        json={
            "getEventsResponse": {
                "GetEventsResult": [
                    {
                        "activity": "test",
                        "date": "",
                        "location": "",
                        "reason": "",
                        "traceCode": None,
                    },
                ],
            },
        },
    )
    events = tracker.get_events("LABEL")
    assert events[0].date is None


def test_is_delivered_true(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/CheckStatusDelivered",
        json={"checkStatusDeliveredResponse": {"checkStatusDeliveredResult": True}},
    )
    assert tracker.is_delivered("LABEL") is True


def test_is_delivered_false(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/CheckStatusDelivered",
        json={"checkStatusDeliveredResponse": {"checkStatusDeliveredResult": False}},
    )
    assert tracker.is_delivered("LABEL") is False


def test_is_delivered_missing_key_returns_false(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/CheckStatusDelivered",
        json={"checkStatusDeliveredResponse": {}},
    )
    assert tracker.is_delivered("LABEL") is False


def test_get_item_summary_success(httpx_mock, tracker: AnPostTracker) -> None:
    payload = {
        "getItemSummaryResponse": {
            "GetItemSummaryResult": [
                {
                    "anPostNo": "LABEL",
                    "countryOfOrigin": "AUSTRALIA",
                    "date": "2026-06-04T04:22:48",
                    "deliveryRecordFlag": True,
                    "geisDeliveryName": "",
                    "geisDeliveryOffice": "",
                    "location": "",
                    "reason": "",
                    "receiverName": "",
                    "senderNo": "LABEL",
                    "status": "Delivered",
                },
            ],
        },
    }
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetItemSummary",
        json=payload,
    )
    summaries = tracker.get_item_summary("LABEL")
    assert len(summaries) == 1
    s = summaries[0]
    assert isinstance(s, ItemSummary)
    assert s.an_post_no == "LABEL"
    assert s.country_of_origin == "AUSTRALIA"
    assert s.date == datetime(2026, 6, 4, 4, 22, 48)
    assert s.delivery_record_flag is True
    assert s.status == "Delivered"


def test_get_item_summary_missing_key_returns_empty(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetItemSummary",
        json={"getItemSummaryResponse": {}},
    )
    assert tracker.get_item_summary("LABEL") == []


def test_track_returns_tracking_result(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        json={"getEventsResponse": {"GetEventsResult": []}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetItemSummary",
        json={"getItemSummaryResponse": {"GetItemSummaryResult": []}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/CheckStatusDelivered",
        json={"checkStatusDeliveredResponse": {"checkStatusDeliveredResult": False}},
    )

    result = tracker.track("LABEL")
    assert isinstance(result, TrackingResult)
    assert result.tracking_number == "LABEL"
    assert result.delivered is False
    assert result.events == []
    assert result.summary == []


def test_http_error_raises(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        status_code=401,
        text="Unauthorized",
    )
    with pytest.raises(AnPostHTTPError) as exc:
        tracker.get_events("LABEL")
    assert exc.value.status_code == 401


def test_invalid_json_raises_parse_error(httpx_mock, tracker: AnPostTracker) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{tracker._base_url}/GetEvents",
        status_code=200,
        text="not-json",
    )
    with pytest.raises(AnPostParseError):
        tracker.get_events("LABEL")


def test_custom_subscription_key() -> None:
    t = AnPostTracker(subscription_key="custom-key")
    assert t._client.headers["ocp-apim-subscription-key"] == "custom-key"


def test_default_subscription_key(tracker: AnPostTracker) -> None:
    assert tracker._client.headers["ocp-apim-subscription-key"] == "01b0162771e941639046a97936f72e95"
