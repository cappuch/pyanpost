from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any

from anpost import AnPostTracker


def _serialize(obj: Any) -> str:
    def _default(o: Any) -> str:
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "__dataclass_fields__"):
            return {
                k: _default(v) if hasattr(v, "__dataclass_fields__") or isinstance(v, datetime) else v
                for k, v in o.__dict__.items()
                if k != "raw"
            }
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, default=_default, indent=2, ensure_ascii=False)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: anpost-track <tracking_number>", file=sys.stderr)
        sys.exit(1)

    tracking_number = sys.argv[1]
    tracker = AnPostTracker()
    result = tracker.track(tracking_number)
    print(_serialize(result))


if __name__ == "__main__":
    main()
