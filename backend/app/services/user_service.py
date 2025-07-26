from app.models.user import User
from app.schemas.user import UserCreate
from app.db.database import SessionLocal

def create_user(db: SessionLocal, user: UserCreate):
    db_user = User(name=user.name, email=user.email, hashed_password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
