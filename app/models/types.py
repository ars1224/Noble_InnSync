from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy.types import Date, Numeric, TypeDecorator


def utc_now():
    return datetime.now(timezone.utc)


class ISODate(TypeDecorator):
    """Store a real DATE while accepting existing ISO-formatted inputs."""

    impl = Date
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None or isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as error:
            raise ValueError("Dates must use the YYYY-MM-DD format.") from error


class Money(TypeDecorator):
    """Store currency as fixed-precision NUMERIC values."""

    impl = Numeric(12, 2)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        try:
            return Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Money values must be numeric.") from error
