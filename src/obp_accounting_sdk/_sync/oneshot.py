"""Oneshot session."""

import logging
from http import HTTPStatus
from types import TracebackType
from typing import Self
from uuid import UUID

import httpx

from obp_accounting_sdk.constants import ServiceSubtype, ServiceType
from obp_accounting_sdk.errors import (
    AccountingReservationError,
    AccountingUsageError,
    InsufficientFundsError,
)
from obp_accounting_sdk.utils import get_current_timestamp

L = logging.getLogger(__name__)


class OneshotSession:
    """Oneshot Session."""

    def __init__(
        self,
        http_client: httpx.Client,
        base_url: str,
        subtype: ServiceSubtype | str,
        proj_id: UUID | str,
        count: int,
    ) -> None:
        """Initialization."""
        self._http_client = http_client
        self._base_url: str = base_url
        self._service_type: ServiceType = ServiceType.ONESHOT
        self._service_subtype: ServiceSubtype = ServiceSubtype(subtype)
        self._proj_id: UUID = UUID(str(proj_id))
        self._job_id: UUID | None = None
        self._count = self.count = count

    @property
    def count(self) -> int:
        """Return the count value used for reservation or usage."""
        return self._count

    @count.setter
    def count(self, value: int) -> None:
        """Set the count to be used for usage."""
        if not isinstance(value, int) or value < 0:
            errmsg = "count must be an integer >= 0"
            raise ValueError(errmsg)
        if self.count is not None and self.count != value:
            L.info("Overriding previous count value %s with %s", self.count, value)
        self._count = value

    def _make_reservation(self) -> None:
        """Make a new reservation."""
        if self._job_id is not None:
            errmsg = "Cannot make a reservation more than once"
            raise RuntimeError(errmsg)
        L.info("Making reservation")
        data = {
            "type": self._service_type,
            "subtype": self._service_subtype,
            "proj_id": str(self._proj_id),
            "count": str(self.count),
        }
        try:
            response = self._http_client.post(
                f"{self._base_url}/reservation/oneshot",
                json=data,
            )
            if response.status_code == HTTPStatus.PAYMENT_REQUIRED:
                raise InsufficientFundsError
            response.raise_for_status()
        except httpx.RequestError as exc:
            errmsg = f"Error while requesting {exc.request.url!r}"
            raise AccountingReservationError(errmsg) from exc
        except httpx.HTTPStatusError as exc:
            errmsg = (
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}"
            )
            raise AccountingReservationError(errmsg) from exc
        try:
            self._job_id = UUID(response.json()["job_id"])
        except Exception as exc:
            errmsg = "Error while parsing the response"
            raise AccountingReservationError(errmsg) from exc

    def _send_usage(self) -> None:
        """Send usage to accounting."""
        if self._job_id is None:
            errmsg = "Cannot send usage before making a successful reservation"
            raise RuntimeError(errmsg)
        L.info("Sending usage")
        data = {
            "type": self._service_type,
            "subtype": self._service_subtype,
            "proj_id": str(self._proj_id),
            "count": str(self.count),
            "job_id": str(self._job_id),
            "timestamp": get_current_timestamp(),
        }
        try:
            response = self._http_client.post(f"{self._base_url}/usage/oneshot", json=data)
            response.raise_for_status()
        except httpx.RequestError as exc:
            errmsg = f"Error while requesting {exc.request.url!r}"
            raise AccountingUsageError(errmsg) from exc
        except httpx.HTTPStatusError as exc:
            errmsg = (
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}"
            )
            raise AccountingUsageError(errmsg) from exc

    def __enter__(self) -> Self:
        """Initialize when entering the context manager."""
        self._make_reservation()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Cleanup when exiting the context manager."""
        if exc_type is None:
            self._send_usage()
        else:
            L.warning(f"Unhandled exception {exc_type.__name__}, not sending usage")
