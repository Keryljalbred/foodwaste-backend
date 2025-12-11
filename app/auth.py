from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from .database import SessionLocal
from .models import User
from .schemas import UserCreate
from . import models
import os

# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET", "super_secret_key")
ALGORITHM = os.getenv("JWT_ALGO", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Gestion des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # S'assurer qu'on reçoit bien une string et la tronquer à 72 caractères
    if not isinstance(password, str):
        password = str(password)
    password = password[:72]
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if not isinstance(password, str):
        password = str(password)
    return pwd_context.verify(password[:72], hashed)

def create_access_token(user_id: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

