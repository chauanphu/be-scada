# dependencies.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user  # Assuming this function is already defined
from models.Account import Account, Role
from database.session import get_db
from config import PermissionEnum

def admin_required(
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get the role name of the current user
    role_name = db.query(Role).filter(Role.role_id == current_user.role).first().role_name
    if role_name not in ["ADMIN", "SUPERADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view or edit ADMIN or SUPERADMIN roles."
        )
    return current_user

def required_permission(permission: PermissionEnum):
    def check_permission(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Get all permission names of the current user
        permissions = db.query(Role).filter(Role.role_id == current_user.role).first().permissions
        permission_names = [permission.permission_name for permission in permissions]
        if permission.value not in permission_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user
    return check_permission