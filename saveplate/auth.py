from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from saveplate.config import settings
from saveplate.database import ManagedTransaction, transactional
from typing import Literal
from datetime import date

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class User(BaseModel):
    email: EmailStr
    name: str
    gender: Literal["male", "female", "other"] | None = None
    birth_date: date | None = None
    join_date: date
    disabled: bool = False

    class Config:
        from_attributes = True

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@transactional("read")
def get_user(tx: ManagedTransaction, email: str):
    result = tx.run("MATCH (u:User {email: $email}) RETURN u", email=email)
    user = result.single()
    if user:
        user_data = dict(user["u"])
        user_data["birth_date"] = user_data["birth_date"].to_native() if user_data["birth_date"] else None
        user_data["join_date"] = user_data["join_date"].to_native()
        return User(**user_data)


def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
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
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@transactional("write")
def save_refresh_token(tx: ManagedTransaction, email: str, refresh_token: str):
    tx.run(
        "MATCH (u:User {email: $email}) "
        "SET u.refresh_token = $refresh_token",
        email=email, refresh_token=refresh_token
    )

@transactional("read")
def get_user_by_refresh_token(tx: ManagedTransaction, refresh_token: str):
    result = tx.run(
        "MATCH (u:User {refresh_token: $refresh_token}) RETURN u",
        refresh_token=refresh_token
    )
    user = result.single()
    if user:
        return User(**user["u"])

def create_token_pair(email: str):
    access_token = create_access_token(data={"sub": email})
    refresh_token = create_refresh_token(data={"sub": email})
    save_refresh_token(email, refresh_token)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@transactional("write")
def create_user(tx: ManagedTransaction, email: str, password: str, name: str, gender: str | None = None, birth_date: date | None = None):
    hashed_password = get_password_hash(password)
    join_date = date.today()
    
    result = tx.run("""
    CREATE (u:User {
        email: $email,
        hashed_password: $hashed_password,
        name: $name,
        gender: $gender,
        birth_date: $birth_date,
        join_date: $join_date,
        disabled: false
    })
    RETURN u
    """, email=email, hashed_password=hashed_password, name=name, gender=gender, birth_date=birth_date, join_date=join_date)
    
    user = result.single()
    if user:
        user_data = dict(user["u"])
        user_data["birth_date"] = user_data["birth_date"].to_native() if user_data["birth_date"] else None
        user_data["join_date"] = user_data["join_date"].to_native()
        return User(**user_data)
    else:
        raise HTTPException(status_code=400, detail="Failed to create user")
