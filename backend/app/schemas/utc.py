from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer


def _to_naive_utc(value: datetime) -> datetime:
    """
    Store every datetime as naive UTC.

    - Aware values (e.g. "2026-10-04T12:30:00.000Z") are converted to UTC.
    - Naive values are assumed to already be UTC.
    """
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)

    return value


def _to_utc_string(value: datetime) -> str:
    """
    Send datetimes to the browser with an explicit "Z" so that
    JavaScript converts them to the viewer's local time correctly.
    """
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)

    return value.isoformat() + "Z"


UTCDateTime = Annotated[
    datetime,
    AfterValidator(_to_naive_utc),
    PlainSerializer(
        _to_utc_string,
        return_type=str,
        when_used="json",
    ),
]
