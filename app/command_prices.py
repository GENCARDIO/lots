def command_price(command, lot, field):
    """Use the order's saved price, or the current catalog price for old orders."""
    price = getattr(command, field, None) if command is not None else None
    return getattr(lot, field, None) if price in (None, '') else price
