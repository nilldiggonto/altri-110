"""Minimal signed session token: "<user_id>.<hmac>". Sign-up is out of scope; login is a seeded user pick."""
import hashlib
import hmac

from app.core.config import settings


def _sig(user_id: str) -> str:
    return hmac.new(settings.secret_key.encode(), user_id.encode(), hashlib.sha256).hexdigest()


def issue_token(user_id: str) -> str:
    return f"{user_id}.{_sig(user_id)}"


def verify_token(token: str) -> str | None:
    user_id, _, sig = token.rpartition(".")
    return user_id if user_id and hmac.compare_digest(sig, _sig(user_id)) else None
