from __future__ import annotations

from datetime import timezone, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_timezone(name: str = "Asia/Amman") -> tzinfo:
    """
    Return a timezone object.

    On Windows Store Python installations, the standard library zoneinfo module
    often cannot find IANA timezone data unless the PyPI package `tzdata` is
    installed. This helper first tries the real IANA zone, then falls back to a
    fixed UTC+03:00 timezone for Amman so the MVP can still run immediately.
    """
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == "Asia/Amman":
            return timezone(timedelta(hours=3), name="Asia/Amman")
        return timezone.utc
