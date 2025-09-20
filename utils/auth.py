from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

from models.user import User
from models.database import get_supabase_client

load_dotenv()

# JWT configuration
SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET", "fallback-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from Supabase
    supabase = get_supabase_client()
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    
    if not response.data:
        raise credentials_exception
    
    user_data = response.data[0]
    return User(**user_data)

def verify_password(plain_password, hashed_password):
    # Supabase handles password verification through its auth system
    # This is a placeholder for any additional password verification needed
    return True

def get_password_hash(password):
    # Supabase handles password hashing through its auth system
    # This is a placeholder for any additional password hashing needed
    return password
