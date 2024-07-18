# Custom exceptions

class NotHexError(Exception):
    """Character not in 0-9 or a-f"""
    pass


class NotBase32Error(Exception):
    """Character not in 0-9 or a-v"""
    pass