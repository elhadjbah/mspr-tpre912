import os
from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select
import json
import qrcode
import base64
import hashlib
from io import BytesIO
from datetime import datetime, timedelta
from uuid import uuid4
from cryptography.fernet import Fernet


class User(SQLModel, table=False):
    __tablename__ = "users"  # Match your existing table name

    id: Optional[int] = Field(default=None, primary_key=True)
    username : str
    password: str = Field(default=None)
    mfa: str = Field(default=None)
    gendate : datetime = Field(default=None)
    expired: bool = Field(default=False)


# Database configuration for serverless
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cofrap:cofrap123@localhost/cofrap")

# Connection pool settings optimized for serverless
engine = create_engine(
    DATABASE_URL,
    pool_size=1,  # Small pool for serverless
    max_overflow=0,  # No overflow connections
    pool_pre_ping=True,  # Validate connections
    pool_recycle=300,  # Recycle connections every 5 minutes
    connect_args={
        "connect_timeout": 10,
        "server_settings": {
            "application_name": "password_generator",
        }
    }
)


def get_session():
    """Get database session - use this pattern in serverless functions"""
    return Session(engine)


def get_all_users(limit: int = 10) -> List[User]:
    """Get all users with limit"""
    with get_session() as session:
        statement = session.query(User()).limit(limit)
        results = session.exec(statement).all()
        return results

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
    with get_session() as session:
        user = User()
        user.username = username
        user.password = encrypted_password
        user.gendate = gendate
        session.add(user)
        session.commit()
        return user.id
def create_user(event, context):
    try:
        try:
            body = event.body
            bodyJson = json.loads(body)
            print(bodyJson)

        except Exception as e:
            return {
                "statusCode": 400,
                "body": {"error": f"Requête JSON invalide {body}" }
            }

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

        return {
            "statusCode": 200,
            "body": {
                "success": True,
                "userId": user_id,
                "password": password,
                "qrCode": img_base64,
                "encryptedPassword": encrypted_pw,
                "expiresAt": now + timedelta(days=180),
                "message": "Mot de passe généré avec succès"
            },
            "headers": {
                "Content-Type": "application/json"
            }
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }


def handle(event, context):
    try:
        return create_user(event, context)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }
