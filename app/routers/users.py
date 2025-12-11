from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal, get_db
from .. import models
from ..schemas import UserCreate, UserOut
from ..auth import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from ..security import get_current_user
from fastapi import status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


router = APIRouter(prefix="/users", tags=["Users"])

#🚪 Enregistrement et connexion des utilisateurs 
@router.post("/register", response_model=UserOut)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà enregistré")

    hashed_pw = hash_password(payload.password)  # 👈 on hash le mot de passe
    user = models.User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        household_size=payload.household_size
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

#🚪 Connexion des utilisateurs
@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print("📥 FRONT A ENVOYÉ :")
    print("username =", form_data.username)
    print("password =", form_data.password)
    print("client_id =", form_data.client_id)
    print("client_secret =", form_data.client_secret)
    print("grant_type =", form_data.grant_type)

    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        print("❌ Mot de passe invalide OU utilisateur introuvable")
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}

#📋 Obtenir les informations de l'utilisateur courant
@router.get("/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user)):
    return current_user



class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="kiki.updated@example.com")
    full_name: Optional[str] = Field(None, example="Kiki Version 2")
    household_size: Optional[int] = Field(None, example=4)
    password: Optional[str] = Field(None, example="motdepasse123!")

    
#✏️ Mettre à jour les informations de l'utilisateur courant
@router.put("/me", response_model=UserOut)
def update_current_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Mise à jour des champs
    if payload.email:
        existing = db.query(models.User).filter(models.User.email == payload.email).first()
        if existing and existing.id != user.id:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        user.email = payload.email

    if payload.full_name:
        user.full_name = payload.full_name

    if payload.household_size:
        user.household_size = payload.household_size

    if payload.password:
        user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return user


#🗑️ Supprimer le compte de l'utilisateur courant
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    db.delete(user)
    db.commit()
    return None

#📋 Obtenir les informations de l'utilisateur
@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

