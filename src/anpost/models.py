from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


@dataclass
class TrackingEvent:
    activity: str
    date: datetime | None
    location: str
    reason: str
    trace_code: int | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> TrackingEvent:
        return cls(
            activity=data.get("activity", ""),
            date=_parse_datetime(data.get("date")),
            location=data.get("location", ""),
            reason=data.get("reason", ""),
            trace_code=data.get("traceCode"),
            raw=data,
        )


@dataclass
class ItemSummary:
    an_post_no: str
    country_of_origin: str
    date: datetime | None
    delivery_record_flag: bool
    geis_delivery_name: str
    geis_delivery_office: str
    location: str
    reason: str
    receiver_name: str
    sender_no: str
    status: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ItemSummary:
        return cls(
            an_post_no=data.get("anPostNo", ""),
            country_of_origin=data.get("countryOfOrigin", ""),
            date=_parse_datetime(data.get("date")),
            delivery_record_flag=bool(data.get("deliveryRecordFlag", False)),
            geis_delivery_name=data.get("geisDeliveryName", ""),
            geis_delivery_office=data.get("geisDeliveryOffice", ""),
            location=data.get("location", ""),
            reason=data.get("reason", ""),
            receiver_name=data.get("receiverName", ""),
            sender_no=data.get("senderNo", ""),
            status=data.get("status", ""),
            raw=data,
        )


@dataclass
class TrackingResult:
    tracking_number: str
    delivered: bool
    events: list[TrackingEvent]
    summary: list[ItemSummary]
