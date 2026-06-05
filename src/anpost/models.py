from __future__ import annotations

import enum
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


class MailType(str, enum.Enum):
    LETTER = "LETT"
    FLAT = "FLAT"
    PACKET = "PCKT"
    PARCEL = "PRCL"


@dataclass
class AddOnFeature:
    name: str
    description: str
    rate: float
    code: str
    category_type: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AddOnFeature:
        return cls(
            name=data.get("Name", ""),
            description=data.get("Description", ""),
            rate=data.get("Rate", 0),
            code=data.get("Code", ""),
            category_type=data.get("CategoryType", ""),
            raw=data,
        )


@dataclass
class MailService:
    service_code: str
    service_name: str
    service_description: str
    capture_description: bool
    rate_id: int
    rate_group_id: int
    rate: float
    vat_rate: float
    vat_amount: float
    service_priority: int
    service_features: list[str]
    transit_time_min_days: int
    transit_time_max_days: int
    label_purchase_online: bool
    call_to_action: str | None
    add_on_features: list[AddOnFeature]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MailService:
        features = []
        for key in ("ServiceFeature1", "ServiceFeature2", "ServiceFeature3", "ServiceFeature4", "ServiceFeature5"):
            val = data.get(key)
            if val:
                features.append(val.strip())
        return cls(
            service_code=data.get("ServiceCode", ""),
            service_name=data.get("ServiceName", ""),
            service_description=data.get("ServiceDescription", ""),
            capture_description=bool(data.get("CaptureDescription", False)),
            rate_id=data.get("RateId", 0),
            rate_group_id=data.get("RateGroupId", 0),
            rate=data.get("Rate", 0),
            vat_rate=data.get("VatRate", 0),
            vat_amount=data.get("VatAmount", 0),
            service_priority=data.get("ServicePriority", 0),
            service_features=features,
            transit_time_min_days=data.get("TransitTimeMinDays", 0),
            transit_time_max_days=data.get("TransitTimeMaxDays", 0),
            label_purchase_online=bool(data.get("LabelPurchaseOnline", False)),
            call_to_action=data.get("CallToAction"),
            add_on_features=[AddOnFeature.from_api(f) for f in data.get("AddOnFeatures", [])],
            raw=data,
        )


@dataclass
class RateZone:
    code: str
    name: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> RateZone:
        return cls(
            code=data.get("Code", ""),
            name=data.get("Name", ""),
            raw=data,
        )


@dataclass
class PostalRateResponse:
    country_code: str
    country_name: str
    weight: float
    mail_type: str
    session_id: str
    calculator_reference: str
    country_weight_limit: int
    zone: RateZone
    mail_services: list[MailService]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PostalRateResponse:
        return cls(
            country_code=data.get("CountryCode", ""),
            country_name=data.get("CountryName", ""),
            weight=data.get("Weight", 0),
            mail_type=data.get("MailType", ""),
            session_id=data.get("SessionId", ""),
            calculator_reference=data.get("CalculatorReference", ""),
            country_weight_limit=data.get("CountryWeightLimit", 0),
            zone=RateZone.from_api(data.get("Zone", {})),
            mail_services=[MailService.from_api(s) for s in data.get("MailServices", [])],
            raw=data,
        )


@dataclass
class PostalRateResult:
    error_message: str
    session_id: str
    response: PostalRateResponse | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PostalRateResult:
        resp_data = data.get("Response")
        return cls(
            error_message=data.get("ErrorMessage", ""),
            session_id=data.get("SessionId", ""),
            response=PostalRateResponse.from_api(resp_data) if resp_data else None,
            raw=data,
        )
