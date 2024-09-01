from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from saveplate.auth import authenticate_user, create_token_pair, get_user_by_refresh_token, TokenPair
from saveplate.database import transactional

router = APIRouter()

@router.post("/token", response_model=TokenPair)
@transactional("write")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token_pair(user.email)

@router.post("/refresh", response_model=TokenPair)
@transactional("write")
async def refresh_token(refresh_token: str):
    user = get_user_by_refresh_token(refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token_pair(user.email)
