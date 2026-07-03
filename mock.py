"""Common interface for wearable data sources.

Every source (synthetic, Fitbit, HealthKit...) returns the same SleepSession
shape, so the rest of the pipeline never cares where the data came from.
"""

from typing import Protocol

from ...models import SleepSession


class WearableSource(Protocol):
    name: str

    def fetch_night(self, user_id: str, night_date: str) -> SleepSession:
        """Return the sleep session ending on the morning of `night_date`."""
        ...
