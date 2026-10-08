# Custom exceptions for the Car Rental Management System
# These handle specific error conditions across booking and validation

class VehicleNotAvailableError(Exception):
    """Raised when trying to book a vehicle that is already booked or unavailable."""
    pass


class InvalidLicenseError(Exception):
    """Raised when a driving license number does not match the required format."""
    pass


class InvalidPhoneError(Exception):
    """Raised when a phone number is not a valid 10-digit number."""
    pass


class InvalidDatesError(Exception):
    """Raised when booking dates are illogical (e.g. return date before start date)."""
    pass


class CustomerNotFoundError(Exception):
    """Raised when a requested customer ID does not exist in the database."""
    pass
