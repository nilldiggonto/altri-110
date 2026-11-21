import uuid


def new_id(prefix: str):
    """Seed ids are kept (u1, t12). New rows get prefix + short uuid."""
    return lambda: f"{prefix}_{uuid.uuid4().hex[:12]}"
