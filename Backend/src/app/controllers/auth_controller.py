# File: application/src/app/controllers/auth_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta
from random import randint
import os
from uuid import uuid4

from src.app.db.session import get_db
from src.app.models.user import User
from src.app.models.password_reset import PasswordReset
from src.app.schemas.user import UserCreate, UserRead
from src.app.schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from src.app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from src.app.utils.email import send_reset_pin_email

router = APIRouter()

@router.post("/signup", response_model=UserRead)
def signup(
    user: UserCreate,
    session: Session = Depends(get_db)
):
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Email already registered"
        )

    # 1️⃣ Create the User
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user

@router.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db)
):
    print("--- STUDENT LOGIN FUNCTION STARTED ---")
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"user_id": str(user.id), "role": user.role})

    # Create the response content
    content = {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "message": "Login successful."
    }

    return JSONResponse(content=content)

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse
)
def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db)
):
    # Check if user exists and is active
    user = session.exec(
        select(User)
        .where(User.email == request.email)
        .where(User.is_active == True)
    ).first()

    if not user:
        # Return a user-friendly message for non-existent or inactive users
        return {
            "message": "This email is not registered in our system. Please check the email address or sign up for a new account.",
            "status": "not_found"
        }

    # Generate a 6-digit PIN
    pin = f"{randint(100000, 999999)}"
    
    # Create password reset record
    reset = PasswordReset(
        user_id=user.id,
        pin=pin,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    
    # Invalidate any existing unused PINs for this user
    existing_resets = session.exec(
        select(PasswordReset)
        .where(PasswordReset.user_id == user.id)
        .where(PasswordReset.used == False)
        .where(PasswordReset.expires_at > datetime.utcnow())
    ).all()
    
    for existing in existing_resets:
        existing.used = True
        session.add(existing)
    
    # Add new reset record
    session.add(reset)
    session.commit()
    
    # Send email in background
    background_tasks.add_task(send_reset_pin_email, user.email, pin)
    
    # Return success message for valid users
    return {
        "message": "We've sent a password reset PIN to your email. Please check your inbox and spam folder.",
        "status": "sent"
    }

@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse
)
def reset_password(
    data: ResetPasswordRequest,
    session: Session = Depends(get_db)
):
    # First check if user exists
    user = session.exec(
        select(User)
        .where(User.email == data.email)
        .where(User.is_active == True)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address. Please check your email and try again."
        )
    
    # Check for valid, unused, and non-expired PIN
    reset = session.exec(
        select(PasswordReset)
        .where(
            PasswordReset.user_id == user.id,
            PasswordReset.pin == data.pin,
            PasswordReset.used == False,
            PasswordReset.expires_at >= datetime.utcnow()
        )
        .order_by(PasswordReset.created_at.desc())
    ).first()
    
    if not reset:
        # Check if PIN exists but is expired
        expired_reset = session.exec(
            select(PasswordReset)
            .where(
                PasswordReset.user_id == user.id,
                PasswordReset.pin == data.pin,
                PasswordReset.used == False,
                PasswordReset.expires_at < datetime.utcnow()
            )
        ).first()
        
        if expired_reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The PIN has expired. Please request a new password reset PIN."
            )
        
        # Check if PIN exists but was already used
        used_reset = session.exec(
            select(PasswordReset)
            .where(
                PasswordReset.user_id == user.id,
                PasswordReset.pin == data.pin,
                PasswordReset.used == True
            )
        ).first()
        
        if used_reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This PIN has already been used. Please request a new password reset PIN."
            )
        
        # If none of the above, PIN is invalid
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PIN. Please check the PIN and try again."
        )
    
    # Update password and mark PIN as used
    user.hashed_password = hash_password(data.new_password)
    reset.used = True
    session.add(user)
    session.add(reset)
    session.commit()
    
    return {
        "message": "Your password has been successfully reset. You can now login with your new password.",
        "status": "success"
    }

@router.post("/logout")
def logout():
    # The client is responsible for deleting the token.
    return {"message": "Successfully logged out"}