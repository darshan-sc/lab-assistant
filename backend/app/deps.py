from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import SessionLocal
from app.core.config import settings
from app.models.user import User

import requests
from jose import jwk

# Simple in-memory cache for JWKS
jwks_cache = {}

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_supabase_jwks_key(kid: str) -> str:
    """
    Fetch JWKS from Supabase and return the PEM key for the given kid.
    """
    global jwks_cache
    
    # Check cache first
    if kid in jwks_cache:
        return jwks_cache[kid]
    
    # Fetch from Supabase
    if not settings.SUPABASE_URL:
        # Fallback to secret if no URL
        return settings.SUPABASE_JWT_SECRET
        
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
        jwks = response.json()
        
        for key_data in jwks.get("keys", []):
            if key_data.get("kid") == kid:
                key = jwk.construct(key_data)
                pem = key.to_pem().decode("utf-8")
                jwks_cache[kid] = pem
                return pem
                
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        
    return settings.SUPABASE_JWT_SECRET

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate Supabase JWT and return the current user.
    Creates the user if they don't exist (first login).
    """
    token = credentials.credentials

    try:
        # Get kid from header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "HS256")
        
        if alg == "HS256":
            key = settings.SUPABASE_JWT_SECRET
        else:
            # For ES256/RS256, use JWKS
            if kid:
                key = get_supabase_jwks_key(kid)
            else:
                 key = settings.SUPABASE_JWT_PUBLIC_KEY or settings.SUPABASE_JWT_SECRET
        
        payload = jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience="authenticated",
        )
    except JWTError as e:
        try:
            unverified_header = jwt.get_unverified_header(token)
            print(f"DEBUG: Token Header: {unverified_header}")
        except:
            print("DEBUG: Could not decode token header")
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    supabase_uid = payload.get("sub")
    email = payload.get("email")

    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
        )

    # Get or create user - check by supabase_uid first, then by email
    stmt = select(User).where(User.supabase_uid == supabase_uid)
    user = db.execute(stmt).scalar_one_or_none()

    if not user and email:
        # Check if user exists by email (supabase_uid may have changed)
        stmt = select(User).where(User.email == email)
        user = db.execute(stmt).scalar_one_or_none()
        if user:
            user.supabase_uid = supabase_uid
            db.commit()
            db.refresh(user)

    if not user:
        # First login - create user
        user = User(supabase_uid=supabase_uid, email=email or "")
        db.add(user)
        db.commit()
        db.refresh(user)
    elif email and user.email != email:
        # Update email if changed
        user.email = email
        db.commit()
        db.refresh(user)

    return user
