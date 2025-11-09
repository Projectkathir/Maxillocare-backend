from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
from models.user import User

# Configure password hashing with explicit bcrypt settings for Python 3.13
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash with proper error handling"""
    try:
        # Ensure password is properly encoded and truncated to 72 bytes
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate to 72 bytes and decode back to string
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password with proper truncation for bcrypt 72-byte limit"""
    try:
        # Encode password to bytes to check actual byte length
        password_bytes = password.encode('utf-8')
        
        # Bcrypt has a 72-byte limit, truncate if necessary
        if len(password_bytes) > 72:
            # Truncate to 72 bytes and decode back to string
            truncated_password = password_bytes[:72].decode('utf-8', errors='ignore')
        else:
            truncated_password = password
        
        # Hash the password
        return pwd_context.hash(truncated_password)
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        raise ValueError(f"Unable to hash password: {str(e)}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def get_current_doctor(current_user: User = Depends(get_current_user)) -> User:
    """Verify current user has doctor role"""
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Doctor access required."
        )
    return current_user


def get_current_patient(current_user: User = Depends(get_current_user)) -> User:
    """Verify current user has patient role"""
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Patient access required."
        )
    return current_user
