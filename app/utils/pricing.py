from datetime import date, datetime
from decimal import Decimal


DATE_FORMAT = "%Y-%m-%d"


def calculate_nights(check_in, check_out):
    if not check_in or not check_out:
        raise ValueError("Check-in and check-out dates are required.")

    try:
        check_in_date = (
            check_in if isinstance(check_in, date)
            else datetime.strptime(check_in, DATE_FORMAT).date()
        )
        check_out_date = (
            check_out if isinstance(check_out, date)
            else datetime.strptime(check_out, DATE_FORMAT).date()
        )
    except ValueError as error:
        raise ValueError("Dates must use the YYYY-MM-DD format.") from error

    nights = (check_out_date - check_in_date).days

    if nights < 1:
        raise ValueError("Check-out date must be after check-in date.")

    return nights


def calculate_stay_total(nightly_total, check_in, check_out):
    nights = calculate_nights(check_in, check_out)
    total = Decimal(str(nightly_total)) * nights
    return nights, total.quantize(Decimal("0.01"))
