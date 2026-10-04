import hashlib
import secrets

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import UserSession


SESSION_DAYS = 7


def normalize_name_id(name_id: str) -> str:
    return name_id.strip().lower()


def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_session(
    db: Session,
    user: User,
) -> str:

    raw_token = secrets.token_urlsafe(48)

    token_hash = hash_token(raw_token)

    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow()
        + timedelta(days=SESSION_DAYS),
    )

    db.add(session)
    db.commit()

    return raw_token


def get_user_from_token(
    db: Session,
    token: str,
):

    if not token:
        return None

    token_hash = hash_token(token)

    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
        )
        .first()
    )

    if not session:
        return None

    if session.expires_at < datetime.utcnow():
        return None

    return (
        db.query(User)
        .filter(User.id == session.user_id)
        .first()
    )


def revoke_session(
    db: Session,
    token: str,
):

    token_hash = hash_token(token)

    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
        )
        .first()
    )

    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()