# from models.user import User
from models.Account import Account, Role, Permission
from models.Status import *
from models.Task import *
from models.unit import *
from models.Audit import *

from utils import hash_password  # For hashing the password
from config import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL, SUPERADMIN_USERNAME, SUPERADMIN_PASSWORD, SUPERADMIN_EMAIL, PermissionEnum
# create_roles.py

from database import SessionLocal
from database.session import session

def create_default_permissions():
    session = SessionLocal()
    try:
        for permission in PermissionEnum:
            permission_name = permission.value
            existing_permission = session.query(Permission).filter(Permission.permission_name == permission_name).first()
            if not existing_permission:
                new_permission = Permission(permission_name=permission_name)
                session.add(new_permission)
                session.commit()

    except Exception as e:
        session.rollback()
        print(f"Error creating permissions: {e}")
    finally:
        session.close()

def create_default_roles(): 
    session = SessionLocal()
    try:
        role = ["ADMIN", "SUPERADMIN"]
        for role_name in role:
            existing_role = session.query(Role).filter(Role.role_name == role_name).first()
            if not existing_role:
                new_role = Role(role_name=role_name, rank=1)
                session.add(new_role)
                session.commit()
                # Assign all permissions to the admin role
                all_permissions = session.query(Permission).all()
                new_role.permissions = all_permissions
                session.commit()
            else:
                # Update the rank of the role
                existing_role.rank = 1
                
    except Exception as e:
        session.rollback()
        print(f"Error creating roles: {e}")
    finally:
        session.close()

def create_default_admin():
    session = SessionLocal()
    try:
        # Get the admin role
        admin_role = session.query(Role).filter(Role.role_name == "ADMIN").first()
        superadmin_role = session.query(Role).filter(Role.role_name == "SUPERADMIN").first()

        # Check if admin user already exists
        admin_user = session.query(Account).filter(Account.username == ADMIN_USERNAME).first()
        if not admin_user:
            # Hash the admin password
            hashed_pwd = hash_password(ADMIN_PASSWORD)
            # Create a new admin Account instance
            new_admin = Account(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                password=hashed_pwd,
                role=admin_role.role_id if admin_role else None,
            )
            # Add and commit the new admin user to the database
            session.add(new_admin)
            session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")

        # Check if superadmin user already exists
        superadmin_user = session.query(Account).filter(Account.username == SUPERADMIN_USERNAME).first()
        if not superadmin_user:
            # Hash the superadmin password
            hashed_pwd = hash_password(SUPERADMIN_PASSWORD)
            # Create a new superadmin Account instance
            new_superadmin = Account(
                email=SUPERADMIN_EMAIL,
                username=SUPERADMIN_USERNAME,
                password=hashed_pwd,
                role=superadmin_role.role_id if superadmin_role else None,
            )
            # Add and commit the new superadmin user to the database
            session.add(new_superadmin)
            session.commit()
            print("Superadmin user created successfully.")
        else:
            print("Superadmin user already exists.")
    except Exception as e:
        session.rollback()
        print(f"Error creating admin or superadmin user: {e}")
    finally:
        session.close()

side_roles = {
    "Quản lý thiết bị": ([PermissionEnum.CONFIG_DEVICE, PermissionEnum.CONTROL_DEVICE], 3),
    "Quản lý người dùng": ([PermissionEnum.MANAGE_USER], 2),
    "Quan sát viên": ([PermissionEnum.MONITOR_SYSTEM, PermissionEnum.REPORT, PermissionEnum.VIEW_CHANGE_LOG], 3)
}

def create_side_roles():
    session = SessionLocal()
    try:
        for role_name, (permissions, rank) in side_roles.items():
            existing_role = session.query(Role).filter(Role.role_name == role_name).first()
            existing_permissions = session.query(Permission).filter(Permission.permission_name.in_([permission.value for permission in permissions])).all()
            if not existing_role:
                new_role = Role(role_name=role_name)
                session.add(new_role)
                session.commit()
                # Assign permissions to the role
                if existing_permissions and len(existing_permissions) == len(permissions):
                    new_role.rank = rank
                    new_role.permissions = existing_permissions
                session.commit()
            else:
                if existing_permissions and len(existing_permissions) == len(permissions):
                    existing_role.rank = rank
                    existing_role.permissions = existing_permissions
                session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error creating side roles: {e}")
    finally:
        session.close()

def populate_task_types():
    for task_type in TaskTypeEnum:
        existing_type = session.query(TaskType).filter(TaskType.key == task_type.name).first()
        if not existing_type:
            new_type = TaskType(key=task_type.name, value=task_type.value)
            session.add(new_type)
            session.commit()
            print(f"Added task type {task_type.name} to the database.")
    print("Task types populated successfully.")
