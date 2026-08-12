import secrets
import hashlib


def generate_invitation_token():
    """
    Generates a secure random invitation token.
    """

    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    return token, token_hash