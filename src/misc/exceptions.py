# Custom exceptions

class NotHexError(Exception):
    """Character not in 0-9 or a-f"""
    pass

class NotBase32Error(Exception):
    """Character not in 0-9 or a-v"""
    pass

class CoilsnakeResourceNotFoundError(Exception):
    """Coilsnake resource key not found in Project.snake"""
    
class SubResourceNotFoundError(Exception):
    """Sub-resource (eg. sprite) not found"""
    # CoilsnakeResourceNotFoundError gets caught and a generic error is produced. This hides things like sprite IDs.