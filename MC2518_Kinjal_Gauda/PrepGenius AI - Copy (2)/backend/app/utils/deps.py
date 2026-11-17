from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.utils.security import decode_access_token
from app.utils.exceptions import PrepGeniusException

security_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise PrepGeniusException(
            message="Authentication credentials were not provided",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise PrepGeniusException(
            message="Invalid or expired access token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise PrepGeniusException(
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

    if not user.is_active:
        raise PrepGeniusException(
            message="Inactive user account",
            status_code=status.HTTP_403_FORBIDDEN
        )

    return user
