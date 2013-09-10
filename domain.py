"""Code specific to our domain/business logic"""

def is_valid_group(destination):
    """Return true if destination is a valid known group"""
    # TODO: for now we just check if this is not an email
    if '@' in destination:  # is this an email ?
        return False
    else:
        return True
