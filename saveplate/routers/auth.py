from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from neo4j import ManagedTransaction
from saveplate.auth import authenticate_user, create_token_pair, get_user_by_refresh_token, TokenPair, create_user
from saveplate.database import transactional
from saveplate.model import UserCreate
from pydantic import BaseModel
from datetime import date
import logging

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

logger = logging.getLogger(__name__)

@router.post("/token", response_model=TokenPair)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    사용자 로그인을 처리하고 액세스 토큰과 리프레시 토큰을 발급합니다.

    Args:
        form_data (OAuth2PasswordRequestForm): 사용자 이름과 비밀번호를 포함한 폼 데이터

    Returns:
        TokenPair: 액세스 토큰과 리프레시 토큰

    Raises:
        HTTPException: 인증 실패 시 401 Unauthorized 에러 발생
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token_pair(user.email)

@router.post("/refresh", response_model=TokenPair)
def refresh_token(refresh_token: str):
    """
    리프레시 토큰을 사용하여 새로운 액세스 토큰과 리프레시 토큰을 발급합니다.

    Args:
        refresh_token (str): 유효한 리프레시 토큰

    Returns:
        TokenPair: 새로운 액세스 토큰과 리프레시 토큰

    Raises:
        HTTPException: 유효하지 않은 리프레시 토큰일 경우 401 Unauthorized 에러 발생
    """
    user = get_user_by_refresh_token(refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token_pair(user.email)

@router.post("/register", response_model=TokenPair)
def register_user(user_data: UserCreate):
    """
    새로운 사용자를 등록하고 액세스 토큰과 리프레시 토큰을 발급합니다.

    Args:
        user_data (UserCreate): 새 사용자의 정보 (이메일, 비밀번호, 이름, 성별, 생년월일)

    Returns:
        TokenPair: 새로 생성된 사용자의 액세스 토큰과 리프레시 토큰

    Raises:
        HTTPException: 사용자 생성 실패 시 500 Internal Server Error 발생
    """
    try:
        user = create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            gender=user_data.gender,
            birth_date=user_data.birth_date
        )
        return create_token_pair(user.email)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
