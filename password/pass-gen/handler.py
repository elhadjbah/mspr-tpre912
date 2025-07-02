import os
from typing import Optional
import qrcode
import base64
import hashlib
from io import BytesIO
from datetime import datetime, timedelta
from uuid import uuid4
from cryptography.fernet import Fernet
import json
from sqlmodel import SQLModel, Field, create_engine, Session, select

import logging
logging.basicConfig(level=logging.DEBUG)



class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username : str
    password: str = Field(default=None)
    mfa: str = Field(default=None)
    gendate : datetime = Field(default=None)
    expired: bool = Field(default=False)


# Database configuration for serverless
PGSQL_URL = ""
DATABASE_URL = os.getenv("DATABASE_URL", PGSQL_URL)
logging.debug(f"\nDATABASE_URL : {DATABASE_URL}")

# Connection pool settings optimized for serverless
engine = create_engine(
    DATABASE_URL
)


def get_session():
    """Get database session - use this pattern in serverless functions"""
    return Session(engine)


def update_user_infos(username: str, encrypted_password: str, gendate):
    """Get all users with limit"""
    with get_session() as session:
        stmt = select(User).where(User.username == username)
        existing_user = session.exec(stmt).first()
        logging.debug(f"\nexisting_user : {existing_user}")
        if existing_user is not None:
            existing_user.password = encrypted_password
            existing_user.gendate = gendate
            existing_user.expired = False
            session.commit()
            session.refresh(existing_user)
            return existing_user.id
    return None

class DatabaseManager:
    """Singleton database manager for serverless environments"""
    _instance = None
    _engine = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_engine(self):
        if self._engine is None:
            self._engine = create_engine(
                DATABASE_URL,
                pool_size=1,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=300
            )
        return self._engine

    def get_session(self):
        return Session(self.get_engine())


# Usage with singleton pattern
db_manager = DatabaseManager()


def get_managed_session():
    return db_manager.get_session()

# Configuration (à mettre en variable d’environnement via secrets)
FERNET_KEY = os.environ.get("FERNET_KEY", "aL73p9N9pR0RLW2WETLtMPsnXKvCOf2XRTPbOwJ7Hrs=")

cipher = Fernet(FERNET_KEY.encode())

def generate_strong_password():
    uid = uuid4().hex
    sha = hashlib.sha512(uid.encode()).digest()
    return base64.urlsafe_b64encode(sha)[:24].decode()

def insert_user(username, encrypted_password, gendate):
    user_id = update_user_infos(username, encrypted_password, gendate)
    if user_id is None:
        with get_session() as session:
            user = User(
                username= username,
                password= encrypted_password,
                gendate = gendate,
                mfa= ""
            )
            session.add(user)
            session.commit()
            return user.id
    else:
        return user_id
def create_user(event, context):
    try:
        bodyJson = json.loads(event.body)

        username = bodyJson.get("username")

        if username is None or username == "":
            return {
                "statusCode": 400,
                "body": {"error": "Nom d'utilisateur invalide"}
            }

        password = generate_strong_password()

        encrypted_pw = cipher.encrypt(password.encode()).decode()

        now = datetime.now()
        user_id = insert_user(username, encrypted_pw, now)

        # QR Code en base64
        img = qrcode.make(password)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        response = {
                "success": True,
                "userId": user_id,
                "password": password,
                "qrCode": img_base64,
                "encryptedPassword": encrypted_pw,
                "expiresAt": now + timedelta(days=180),
                "message": "Mot de passe généré avec succès"
            }

        return {
            "statusCode": 200,
            "body": response
        }

    except Exception as e:
        logging.debug(f"\n### ERROR : \n{e}")
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }

def handle(event, context):
    try:
        response = create_user(event, context)
        return response

    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }
