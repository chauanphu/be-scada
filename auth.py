# auth.py

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from models.Account import Account, Role
from utils import verify_password
from database import SessionLocal
from config import SECRET_KEY, ALGORITHM, PermissionEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Account).filter(Account.username == username).first()
    if user and verify_password(password, user.password):
        return user
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Account:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db.query(Account).filter(Account.username == username).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
    
def ws_get_current_user(token: str, db: Session, required_permission: list[PermissionEnum]) -> Account:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db.query(Account).filter(Account.username == username).first()
        if user is None:
            raise credentials_exception
        u_permissions = db.query(Role).filter(Role.role_id == user.role).first().permissions
        u_p_names = set([permission.permission_name for permission in u_permissions])
        # If the current user has none of the required permissions
        required_names = set([p.value for p in required_permission])
        if not required_names.intersection(u_p_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions to access this resource."
            )
        return user
    except JWTError:
        raise credentials_exception