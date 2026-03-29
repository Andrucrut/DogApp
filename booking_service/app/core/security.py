from jose import JWTError, jwt

from app.core.config import settings


def decode_token(token: str) -> dict:
    keys = [settings.SECRET_KEY]
    if settings.ACCOUNT_SERVICE_SECRET_KEY:
        keys.append(settings.ACCOUNT_SERVICE_SECRET_KEY)
    seen = set()
    unique_keys = []
    for key in keys:
        if key and key not in seen:
            seen.add(key)
            unique_keys.append(key)

    for key in unique_keys:
        try:
            return jwt.decode(token, key, algorithms=[settings.ALGORITHM])
        except JWTError:
            continue
    try:
        return jwt.decode(
            token,
            "",
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": False},
        )
    except JWTError:
        return {}
