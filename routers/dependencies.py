# dependencies.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user  # Assuming this function is already defined
from models.Account import Account, Role
from database.session import get_db

def admin_required(
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_name = db.query(Role).filter(Role.role_id == current_user.role).first().role_name
    if role_name == 'user':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user