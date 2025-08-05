from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    print(f"Creating token with expiry: {expire}, data: {data}")
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        username: str = payload.get("username")
        is_anonymous: bool = payload.get("is_anonymous", False)
        
        if user_id_str is None:
            return None
        
        # Convert user_id back to int
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            print(f"Invalid user_id in token: {user_id_str}")
            return None
            
        return {
            "user_id": user_id,
            "username": username, 
            "is_anonymous": is_anonymous
        }
    except JWTError as e:
        print(f"JWT decode error: {e}")
        return None