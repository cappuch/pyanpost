from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
import pytest

from anpost import AnPostTracker
from anpost.client import _RATES_BASE
from anpost.exceptions import AnPostHTTPError, AnPostParseError
from anpost.models import (
    ItemSummary,
    MailType,
    PostalRateResult,
    TrackingEvent,
    TrackingResult,
)


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


def test_get_rates_success(httpx_mock) -> None:
    tracker = AnPostTracker(
        customer_id="test-customer",
        session_id="test-session",
        jwt="test-jwt",
        bearer_token="test-bearer",
    )
    payload = {
        "ErrorMessage": "",
        "SessionId": "test-session",
        "Response": {
            "CountryCode": "IE",
            "CountryName": "Ireland",
            "Weight": 0.1,
            "MailType": "LETT",
            "SessionId": "test-session",
            "CalculatorReference": "CalculatorReference",
            "CountryWeightLimit": 20,
            "Zone": {"Code": "1", "Name": "Ireland"},
            "MailServices": [
                {
                    "ServiceCode": "STDNAT",
                    "ServiceName": "Standard Post",
                    "ServiceDescription": "First Class Delivery Service",
                    "CaptureDescription": False,
                    "RateId": 180292,
                    "RateGroupId": 13,
                    "Rate": 1.85,
                    "VatRate": 0,
                    "VatAmount": 0,
                    "ServicePriority": 1,
                    "ServiceFeature1": "Standard Post",
                    "ServiceFeature2": "No tracking",
                    "TransitTimeMinDays": 1,
                    "TransitTimeMaxDays": 1,
                    "LabelPurchaseOnline": False,
                    "CallToAction": "PurchaseStamps",
                    "AddOnFeatures": [],
                },
            ],
        },
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{_RATES_BASE}/v1/clickpost/rates?countryCode=IE&weight=0.1&mailType=LETT&goods=true",
        json=payload,
    )
    result = tracker.get_rates("IE", 0.1, MailType.LETTER)
    assert isinstance(result, PostalRateResult)
    assert result.error_message == ""
    assert result.response is not None
    assert result.response.country_code == "IE"
    assert len(result.response.mail_services) == 1
    ms = result.response.mail_services[0]
    assert ms.service_code == "STDNAT"
    assert ms.service_name == "Standard Post"
    assert ms.rate == 1.85
    assert ms.transit_time_min_days == 1
    assert ms.transit_time_max_days == 1
    assert ms.add_on_features == []


def test_get_rates_with_string_mail_type(httpx_mock) -> None:
    tracker = AnPostTracker()
    httpx_mock.add_response(
        method="GET",
        url=f"{_RATES_BASE}/v1/clickpost/rates?countryCode=IE&weight=2&mailType=PRCL&goods=true",
        json={
            "ErrorMessage": "",
            "SessionId": "",
            "Response": {
                "CountryCode": "IE",
                "CountryName": "Ireland",
                "Weight": 2,
                "MailType": "PRCL",
                "SessionId": "",
                "CalculatorReference": "CalculatorReference",
                "CountryWeightLimit": 20,
                "Zone": {"Code": "1", "Name": "Ireland"},
                "MailServices": [],
            },
        },
    )
    result = tracker.get_rates("IE", 2, "PRCL")
    assert result.response is not None
    assert result.response.mail_type == "PRCL"


def test_get_rates_with_addons(httpx_mock) -> None:
    tracker = AnPostTracker()
    payload = {
        "ErrorMessage": "",
        "SessionId": "",
        "Response": {
            "CountryCode": "IE",
            "CountryName": "Ireland",
            "Weight": 0.1,
            "MailType": "LETT",
            "SessionId": "",
            "CalculatorReference": "CalculatorReference",
            "CountryWeightLimit": 20,
            "Zone": {"Code": "1", "Name": "Ireland"},
            "MailServices": [
                {
                    "ServiceCode": "REGNAT",
                    "ServiceName": "Registered Post",
                    "ServiceDescription": "Premium Secure Delivery Service",
                    "CaptureDescription": True,
                    "RateId": 180262,
                    "RateGroupId": 13,
                    "Rate": 10,
                    "VatRate": 0,
                    "VatAmount": 0,
                    "ServicePriority": 2,
                    "ServiceFeature1": "Registered Post",
                    "ServiceFeature2": "Tracking",
                    "ServiceFeature5": "Insurance included",
                    "TransitTimeMinDays": 1,
                    "TransitTimeMaxDays": 1,
                    "LabelPurchaseOnline": True,
                    "AddOnFeatures": [
                        {
                            "Name": "Optional Insurance",
                            "Description": "Up to €1500",
                            "Rate": 4.5,
                            "Code": "1",
                            "CategoryType": "INSURANCE",
                        },
                    ],
                },
            ],
        },
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{_RATES_BASE}/v1/clickpost/rates?countryCode=IE&weight=0.1&mailType=LETT&goods=true",
        json=payload,
    )
    result = tracker.get_rates("IE", 0.1, MailType.LETTER)
    ms = result.response.mail_services[0]
    assert ms.service_features == ["Registered Post", "Tracking", "Insurance included"]
    assert len(ms.add_on_features) == 1
    addon = ms.add_on_features[0]
    assert addon.name == "Optional Insurance"
    assert addon.rate == 4.5
    assert addon.category_type == "INSURANCE"


def test_get_rates_no_response(httpx_mock) -> None:
    tracker = AnPostTracker()
    httpx_mock.add_response(
        method="GET",
        url=f"{_RATES_BASE}/v1/clickpost/rates?countryCode=IE&weight=0.1&mailType=LETT&goods=true",
        json={"ErrorMessage": "error", "SessionId": "", "Response": None},
    )
    result = tracker.get_rates("IE", 0.1, MailType.LETTER)
    assert result.error_message == "error"
    assert result.response is None


def test_get_rates_uses_auth_headers() -> None:
    tracker = AnPostTracker(
        rates_subscription_key="rates-key",
        customer_id="cid",
        session_id="sid",
        jwt="myjwt",
        bearer_token="bt",
    )
    assert tracker._rates_subscription_key == "rates-key"
    assert tracker._customer_id == "cid"
    assert tracker._session_id == "sid"
    assert tracker._jwt == "myjwt"
    assert tracker._bearer_token == "bt"


def test_get_rates_sends_auth_headers(httpx_mock) -> None:
    tracker = AnPostTracker(
        customer_id="test-cust",
        session_id="test-sess",
        jwt="test-jwt-val",
        bearer_token="test-bearer-val",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{_RATES_BASE}/v1/clickpost/rates?countryCode=IE&weight=1&mailType=PRCL&goods=false",
        json={
            "ErrorMessage": "",
            "SessionId": "",
            "Response": {
                "CountryCode": "IE",
                "CountryName": "Ireland",
                "Weight": 1,
                "MailType": "PRCL",
                "SessionId": "",
                "CalculatorReference": "CalculatorReference",
                "CountryWeightLimit": 20,
                "Zone": {"Code": "1", "Name": "Ireland"},
                "MailServices": [],
            },
        },
    )
    tracker.get_rates("IE", 1, MailType.PARCEL, goods=False)

    request = httpx_mock.get_request()
    assert request.headers["anp-cp-clickpostbasketciamcustomerid"] == "test-cust"
    assert request.headers["anp-cp-sessionid"] == "test-sess"
    assert request.headers["anp-cp-jwt"] == "test-jwt-val"
    assert request.headers["authorization"] == "Bearer test-bearer-val"
    assert request.headers["ocp-apim-subscription-key"] == "40d54cd8306f42e890831ef7b46bb4f5"


def test_get_rates_default_rates_key(httpx_mock) -> None:
    tracker = AnPostTracker()
    assert tracker._rates_subscription_key == "40d54cd8306f42e890831ef7b46bb4f5"


def test_custom_subscription_key() -> None:
    t = AnPostTracker(subscription_key="custom-key")
    assert t._client.headers["ocp-apim-subscription-key"] == "custom-key"


def test_default_subscription_key(tracker: AnPostTracker) -> None:
    assert tracker._client.headers["ocp-apim-subscription-key"] == "01b0162771e941639046a97936f72e95"
