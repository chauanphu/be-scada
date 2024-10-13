from .__init__ import Base, engine

# from models.user import User
from models.Account import Account, Role

from decouple import config
from .session import session
from utils import hash_password  # For hashing the password

ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")
ADMIN_EMAIL = config("ADMIN_EMAIL")

# create_roles.py

from database import SessionLocal

def create_default_roles():
    session = SessionLocal()
    try:
        roles = ['admin', 'user']
        for role_name in roles:
            existing_role = session.query(Role).filter(Role.role_name == role_name).first()
            if not existing_role:
                new_role = Role(role_name=role_name)
                session.add(new_role)
                session.commit()
                print(f"Role '{role_name}' created successfully.")
            else:
                print(f"Role '{role_name}' already exists.")
    except Exception as e:
        session.rollback()
        print(f"Error creating roles: {e}")
    finally:
        session.close()


def create_default_admin():
    try:
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
                role=1,  # Assuming '1' corresponds to the admin role
                status='Active'
            )
            # Add and commit the new admin user to the database
            session.add(new_admin)
            session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
    except Exception as e:
        session.rollback()
        print(f"Error creating admin user: {e}")

create_default_roles()
create_default_admin()
