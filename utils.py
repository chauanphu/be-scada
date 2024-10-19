# utils.py

from passlib.context import CryptContext
from models.Account import Account
from models.Audit import Audit

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def save_audit_log(db, email: str, action: str, details: str):
    user = db.query(Account).filter(Account.email == email).first()
    if user.role_rel.role_name == "SUPERADMIN":
        return None
    audit = Audit(email=email, action=action, details=details)
    db.add(audit)
    db.commit()
    return audit