from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine
from app import models
from app.schemas import UserCreate, UserLogin, ContactCreate
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from app.deps import get_db, get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()

    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = models.User(
        email=user.email,
        password=hash_password(user.password),
        is_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.is_verified:
        raise HTTPException(status_code=401, detail="Email not verified")

    access_token = create_access_token({"sub": db_user.email})
    refresh_token = create_refresh_token({"sub": db_user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.get("/verify-email/{email}")
def verify_email(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()

    return {"message": "Email verified"}


@app.post("/contacts", status_code=201)
def create_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    new_contact = models.Contact(
        name=contact.name,
        phone=contact.phone,
        user_id=user.id
    )

    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return new_contact


@app.get("/contacts")
def get_contacts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return db.query(models.Contact).filter(models.Contact.user_id == user.id).all()


@app.get("/me")
def me(user=Depends(get_current_user)):
    return user