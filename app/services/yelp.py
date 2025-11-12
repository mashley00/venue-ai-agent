# TEMPORARY: Yelp integration disabled.
# This stub keeps the rest of the app working, but returns no Yelp venues.
# We will replace this later with a geo-filtered Yelp implementation.

def search(*args, **kwargs):
    """Return no Yelp venues (stub)."""
    return []

def search_venues(*args, **kwargs):
    """Alias used in some versions of the code – also returns nothing."""
    return []

