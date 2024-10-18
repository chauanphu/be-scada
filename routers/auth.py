from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from auth import authenticate_user, create_access_token, get_current_user
from database.session import get_db
from pydantic import BaseModel
from models.Account import Account
from models.Audit import ActionEnum, Audit
from schemas import RoleCheck

from config import ACCESS_TOKEN_EXPIRE_MINUTES

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
    audit = Audit(user_id=user.user_id, action=ActionEnum.LOGIN, details=f"User {user.username} logged in")
    db.add(audit)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

## GET ##
@router.get("/role", response_model=RoleCheck)
def read_current_user(current_user: Account = Depends(get_current_user)):
    result = {
        "role": current_user.role,
        "is_admin": current_user.role == 1
    }
    return result