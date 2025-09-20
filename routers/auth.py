from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import logging

from models.user import User, UserCreate, UserRole
from utils.auth import (
    create_access_token, 
    get_password_hash, 
    verify_password,
    get_current_user,
    get_supabase_client
)

router = APIRouter()
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

@router.post("/signup", response_model=dict)
async def signup(user: UserCreate):
    supabase = get_supabase_client()
    
    # Check if user already exists
    existing_user = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user in Supabase Auth
    auth_response = supabase.auth.sign_up({
        "email": user.email,
        "password": user.password,
    })
    
    if auth_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user"
        )
    
    # Create user profile in database
    user_data = {
        "id": auth_response.user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "sport": user.sport,
        "position": user.position,
        "date_of_birth": user.date_of_birth,
        "height": user.height,
        "weight": user.weight
    }
    
    db_response = supabase.table("users").insert(user_data).execute()
    
    if not db_response.data:
        # Rollback auth user creation if profile creation fails
        supabase.auth.admin.delete_user(auth_response.user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user profile"
        )
    
    return {"message": "User created successfully", "user_id": auth_response.user.id}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    supabase = get_supabase_client()
    
    try:
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        if auth_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        access_token = create_access_token(data={"sub": auth_response.user.id})
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/reset-password")
async def reset_password_request(email: str):
    supabase = get_supabase_client()
    
    try:
        # Send password reset email
        supabase.auth.reset_password_email(email)
        return {"message": "Password reset email sent if account exists"}
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        # Don't reveal whether email exists or not
        return {"message": "Password reset email sent if account exists"}

@router.post("/update-password")
async def update_password(token: str, new_password: str):
    supabase = get_supabase_client()
    
    try:
        # Verify token and update password
        supabase.auth.update_user({"password": new_password})
        return {"message": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Password update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
