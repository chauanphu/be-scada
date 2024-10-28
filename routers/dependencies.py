# dependencies.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user  # Assuming this function is already defined
from models.Account import Account, Role
from database.session import get_db
from config import DEBUG, PermissionEnum

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

def required_permission(user_permissions: list[PermissionEnum]):
    def check_permission(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Get all permission names of the current user
        permissions = db.query(Role).filter(Role.role_id == current_user.role).first().permissions
        permission_names = set([permission.permission_name for permission in permissions])
        # If the current user has none of the required permissions
        user_p_names = set([p.value for p in user_permissions])
        if not user_p_names.intersection(permission_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions to access this resource."
            )
        return current_user
    return check_permission