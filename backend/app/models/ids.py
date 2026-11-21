import uuid


def new_id(prefix: str):
    """Seed ids are kept (u1, t12). New rows get prefix + short uuid."""
    return lambda: f"{prefix}_{uuid.uuid4().hex[:12]}"


def as_dict(obj) -> dict:
    """Column values of an ORM row (unlike __dict__, includes unset and expired columns)."""
    return {c.key: getattr(obj, c.key) for c in obj.__mapper__.column_attrs}
