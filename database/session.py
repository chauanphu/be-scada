from database import SessionLocal
from sqlalchemy.orm import Session
from .__init__ import engine

session = Session(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()