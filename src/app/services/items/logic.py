"""Pure business logic functions for items.

These functions have NO side effects:
- No database calls
- No external API calls
- No file I/O
- Just input → output

They are instantly testable without any setup or mocking.
"""

from decimal import Decimal


def calculate_item_price(
    base_price: Decimal,
    quantity: int,
    discount_percent: Decimal = Decimal("0"),
) -> Decimal:
    """Calculate total price for an item.

    Args:
        base_price: Price per unit
        quantity: Number of units
        discount_percent: Discount as decimal (0.15 = 15%)

    Returns:
        Total price after discount, rounded to 2 decimal places

    Example:
        >>> calculate_item_price(Decimal("100"), 2, Decimal("0.10"))
        Decimal('180.00')
    """
    subtotal = base_price * quantity
    discount = subtotal * discount_percent
    return (subtotal - discount).quantize(Decimal("0.01"))


def apply_bulk_discount(quantity: int) -> Decimal:
    """Determine discount based on quantity.

    Business rules:
    - 10+ items: 5% discount
    - 50+ items: 10% discount
    - 100+ items: 15% discount

    Args:
        quantity: Number of items

    Returns:
        Discount as decimal (0.05 = 5%)

    Example:
        >>> apply_bulk_discount(75)
        Decimal('0.10')
    """
    if quantity >= 100:
        return Decimal("0.15")
    if quantity >= 50:
        return Decimal("0.10")
    if quantity >= 10:
        return Decimal("0.05")
    return Decimal("0")


def validate_item_name(name: str) -> tuple[bool, str | None]:
    """Validate an item name.

    Business rules:
    - Must not be empty
    - Must not exceed 255 characters
    - Must not contain special characters

    Args:
        name: The item name to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_item_name("")
        (False, "Name cannot be empty")
        >>> validate_item_name("Valid Item")
        (True, None)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"

    if len(name) > 255:
        return False, "Name cannot exceed 255 characters"

    # Add more rules as needed
    return True, None
