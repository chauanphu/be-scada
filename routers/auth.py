from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from auth import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, create_access_token, get_current_user
from database.session import get_db
from pydantic import BaseModel

from models.Account import Account
from routers.dependencies import admin_required
from schemas import UserCreate, UserRead, UserUpdate
from utils import hash_password

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(form_data.username, form_data.password)
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/user", response_model=UserRead)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db), 
    current_user: Account = Depends(admin_required)
    ):
    # Only admin users can create new users
    if current_user.role != 1:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
    
    db_user = db.query(Account).filter((Account.username == user.username) | (Account.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    hashed_pwd = hash_password(user.password)
    new_user = Account(
        email=user.email,
        username=user.username,
        password=hashed_pwd,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

## GET ##
@router.get("/users/me", response_model=UserRead)
def read_current_user(current_user: Account = Depends(get_current_user)):
    return current_user

@router.get("/user/{user_id}", response_model=UserRead)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: Account = Depends(admin_required)
    ):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users", response_model=list[UserRead])
def read_users(db: Session = Depends(get_db), current_user: Account = Depends(admin_required)):
    users = db.query(Account).all()
    return users

## PUT ##
@router.put("/user/{user_id}", response_model=UserRead)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: Account = Depends(admin_required)):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_update.dict(exclude_unset=True).items():
        if key == "password":
            setattr(user, key, hash_password(value))
        else:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/user/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: Account = Depends(admin_required)
    ):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}