from sqlalchemy.orm import Session
from fastapi import status

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserUpdate
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.exceptions import PrepGeniusException

class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        # Check existing username
        existing_username = db.query(User).filter(User.username == user_in.username).first()
        if existing_username:
            raise PrepGeniusException(
                message="Username is already registered",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check existing email
        existing_email = db.query(User).filter(User.email == user_in.email).first()
        if existing_email:
            raise PrepGeniusException(
                message="Email address is already registered",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user record
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            full_name=user_in.full_name or user_in.username,
            hashed_password=get_password_hash(user_in.password),
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> tuple[User, str]:
        # Allow login by either username or email
        user = db.query(User).filter(
            (User.username == login_data.username_or_email) | 
            (User.email == login_data.username_or_email)
        ).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise PrepGeniusException(
                message="Invalid username/email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            raise PrepGeniusException(
                message="User account is deactivated",
                status_code=status.HTTP_403_FORBIDDEN
            )

        token = create_access_token(subject=user.id)
        return user, token

    @staticmethod
    def update_user_profile(db: Session, user: User, update_data: UserUpdate) -> User:
        if update_data.full_name is not None:
            user.full_name = update_data.full_name

        if update_data.email is not None and update_data.email != user.email:
            existing = db.query(User).filter(User.email == update_data.email).first()
            if existing:
                raise PrepGeniusException("Email already in use", status_code=400)
            user.email = update_data.email

        if update_data.new_password:
            if not update_data.current_password or not verify_password(update_data.current_password, user.hashed_password):
                raise PrepGeniusException("Current password is required and must be correct to set a new password", status_code=400)
            user.hashed_password = get_password_hash(update_data.new_password)

        db.commit()
        db.refresh(user)
        return user
