# pyanpost

`pyanpost` is a python library for tracking an post (irish state-owned postal service) parcels.

## install

```bash
git clone https://github.com/cappuch/pyanpost
cd pyanpost
pip install .
```

## usage

```python
from anpost import AnPostTracker

tracker = AnPostTracker()

# get full tracking result
result = tracker.track("LABEL")
print(result.delivered)

# list tracking events
for event in tracker.get_events("LABEL"):
    print(event.date, event.activity)

# check delivery status
tracker.is_delivered("LABEL")  # -> bool

# get item summary
tracker.get_item_summary("LABEL")  # -> list[ItemSummary]
```

## models

```python
@dataclass
class TrackingEvent:
    activity: str
    date: datetime | None
    location: str
    reason: str
    trace_code: int | None

@dataclass
class ItemSummary:
    an_post_no: str
    country_of_origin: str
    date: datetime | None
    delivery_record_flag: bool
    status: str
    ...

@dataclass
class TrackingResult:
    tracking_number: str
    delivered: bool
    events: list[TrackingEvent]
    summary: list[ItemSummary]
```

## cli

```bash
pip install .
anpost-track LABEL
```

prints json with tracking number, delivery status, events, and summary.

## custom subscription key

```python
tracker = AnPostTracker(subscription_key="your-key-here")
```

## license

mit
