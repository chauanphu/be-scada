from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from auth import authenticate_user, create_access_token, get_current_user
from database.session import get_db
from pydantic import BaseModel
from models.Account import Account, Role
from models.Audit import ActionEnum
from routers.dependencies import required_permission
from schemas import RoleCheck, RoleCreate, RoleRead, RoleReadFull

from config import ACCESS_TOKEN_EXPIRE_MINUTES, PermissionEnum
from utils import save_audit_log

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
    # Create audit log
    action = ActionEnum.LOGIN
    save_audit_log(db, user.email, action, f"{user.username} logged in")

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/")
async def check_token(current_user: Account = Depends(get_current_user)):
    return status.HTTP_200_OK

## GET ##
@router.get("/role/check", response_model=RoleReadFull)
def read_current_user(current_user: Account = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.role_id == current_user.role).first()
    return role