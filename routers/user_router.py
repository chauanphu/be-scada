from fastapi import APIRouter, Depends, HTTPException, status
from auth import get_current_user
from database import session
from .dependencies import required_permission
from config import PermissionEnum
from models.Account import Account, Role
from models.Audit import ActionEnum, Audit
from schemas import RoleRead, UserCreate, UserRead, UserUpdate
from utils import hash_password

router = APIRouter(
    prefix='/user',
    tags=['user'],
    # Only permission MANAGE_USER can access this route
    dependencies=[Depends(required_permission(PermissionEnum.MANAGE_USER))]
)

@router.post("/user", response_model=UserRead)
def create_user(
    user: UserCreate, 
    db: session = Depends(session.get_db), 
    current_user: Account = Depends(get_current_user)
    ):    
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
    # Create audit log
    audit = Audit(user_id=current_user.user_id, action=ActionEnum.CREATE, details=f"User {new_user.username} created")
    db.add(audit)
    db.commit()
    return new_user

def get_all_user_except_superadmin(db: session):
    users = db.query(Account).join(Role).filter(Role.role_name != "SUPERADMIN").all()
    return users

def get_users_with_role(db: session) -> list[UserRead]:
    users = get_all_user_except_superadmin(db)
    return [
        UserRead(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            status=user.status,
            created=user.created,
            updated=user.updated,
            role=RoleRead(
                role_id=user.role_rel.role_id,
                role_name=user.role_rel.role_name
            )
        )
        for user in users
    ]

def protect_admin(db: session, current_user: Account, target_user_id: int):
    # Get role name of the target user
    current_role_name = db.query(Role).filter(Role.role_id == current_user.role).first().role_name
    target_role_name = db.query(Role).join(Account).filter(Account.user_id == target_user_id).first().role_name
    return current_role_name not in ["ADMIN", "SUPERADMIN"] and target_role_name in ["ADMIN", "SUPERADMIN"]

def restrict_self_delete(current_user: Account, target_user_id: int):
    return current_user.user_id == target_user_id

@router.get("/", response_model=list[UserRead])
def read_users(db: session = Depends(session.get_db)):
    # Get all users with their roles
    users = get_users_with_role(db)
    return users

@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int, 
    db: session = Depends(session.get_db),
    current_user: Account = Depends(get_current_user) 
    ):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    protected = protect_admin(db, current_user, user_id)
    if protected:
        raise HTTPException(status_code=403, detail="You cannot view or edit ADMIN or SUPERADMIN roles.")
    
    return UserRead(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        status=user.status,
        created=user.created,
        updated=user.updated,
        role=RoleRead(
            role_id=user.role_rel.role_id,
            role_name=user.role_rel.role_name
        )
    )

## PUT ##
@router.put("/user/{user_id}", response_model=UserRead)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: session = Depends(session.get_db), 
    current_user: Account = Depends(get_current_user)):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if protect_admin(db, current_user, user_id):
        raise HTTPException(status_code=403, detail="You cannot view or edit ADMIN or SUPERADMIN roles.")
    
    for key, value in user_update.dict(exclude_unset=True).items():
        if key == "password":
            setattr(user, key, hash_password(value))
        else:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    # Create audit log
    audit = Audit(user_id=current_user.user_id, action=ActionEnum.UPDATE, details=f"User {user.username} updated")
    db.add(audit)
    db.commit()
    return user

## PATCH ##
@router.patch("/user/{user_id}", response_model=UserRead)
def patch_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: session = Depends(session.get_db), 
    current_user: Account = Depends(get_current_user)):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if protect_admin(db, current_user, user_id):
        raise HTTPException(status_code=403, detail="You cannot view or edit ADMIN or SUPERADMIN roles.")
    update_data = user_update.model_dump(exclude_none=True, exclude_unset=True)
    for key, value in update_data.items():
        if key == "password":
            setattr(user, key, hash_password(value))
        else:
            setattr(user, key, value)
            
    db.commit()
    db.refresh(user)
    # Create audit log
    audit = Audit(user_id=current_user.user_id, action=ActionEnum.UPDATE, details=f"User {user.username} updated")
    db.add(audit)
    db.commit()
    return user

@router.delete("/user/{user_id}")
def delete_user(
    user_id: int, 
    db: session = Depends(session.get_db), 
    current_user: Account = Depends(get_current_user)
    ):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if protect_admin(db, current_user, user_id):
        raise HTTPException(status_code=403, detail="You cannot view or edit ADMIN or SUPERADMIN roles.")
    if restrict_self_delete(current_user, user_id):
        raise HTTPException(status_code=403, detail="You cannot delete yourself.")
    db.delete(user)
    db.commit()
    # Create audit log
    audit = Audit(user_id=current_user.user_id, action=ActionEnum.DELETE, details=f"User {user.username} deleted")
    db.add(audit)
    db.commit()

    return {"detail": "User deleted successfully"}