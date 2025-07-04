# authenticator.py

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from cryptography.fernet import Fernet
from sqlmodel import SQLModel, Field, create_engine, Session, select
import onetimepass as otp
import hashlib

# --- Basic Configuration ---
logging.basicConfig(level=logging.DEBUG)

# --- Environment Variables ---
# Make sure to set these in your OpenFaaS secrets or stack.yml
DATABASE_URL = os.getenv("DATABASE_URL", "")
FERNET_KEY = os.getenv("FERNET_KEY", "aL73p9N9pR0RLW2WETLtMPsnXKvCOf2XRTPbOwJ7Hrs=")

# Initialize Fernet Cipher
cipher = Fernet(FERNET_KEY.encode())


# --- Database Model and Session Management (copied for self-containment) ---

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str = Field(default=None)
    mfa: str = Field(default=None)
    gendate: datetime = Field(default=None)
    expired: bool = Field(default=False)


# Using a singleton pattern for the engine is good practice in serverless
class DatabaseManager:
    _instance = None
    _engine = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_engine(self):
        if self._engine is None:
            logging.info("Creating new database engine instance.")
            self._engine = create_engine(
                DATABASE_URL,
                pool_size=1,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=300  # Recycle connections every 5 minutes
            )
        return self._engine

    def get_session(self):
        return Session(self.get_engine())


db_manager = DatabaseManager()


def get_session():
    return db_manager.get_session()


# --- MFA Verification Logic (copied from mfa-generator.txt) ---

def verify_mfa(username: str, otp_code: str, session: Session):
    """
    Verifies an HOTP or backup code. Modified to accept an active session.
    """
    stmt = select(User).where(User.username == username)
    user = session.exec(stmt).first()

    if not user or not user.mfa:
        return {"statusCode": 404, "body": {"message": "User not found or MFA not configured."}}

    try:
        decrypted_mfa_json = cipher.decrypt(user.mfa.encode()).decode()
        mfa_data = json.loads(decrypted_mfa_json)

        # 1. Verify as primary HOTP code
        is_hotp_valid = otp.valid_hotp(
            token=otp_code,
            secret=mfa_data["secret"].encode('utf-8'),
            last=mfa_data["counter"]
        )

        if is_hotp_valid:
            mfa_data['counter'] += 1
            user.mfa = cipher.encrypt(json.dumps(mfa_data).encode()).decode()
            session.commit()
            return {"statusCode": 200, "verified": True}

        # 2. Verify as a backup code
        hashed_otp = hashlib.sha256(otp_code.encode()).hexdigest()
        if hashed_otp in mfa_data.get("backup_codes_hashed", []):
            mfa_data['backup_codes_hashed'].remove(hashed_otp)
            user.mfa = cipher.encrypt(json.dumps(mfa_data).encode()).decode()
            session.commit()
            return {"statusCode": 200, "verified": True}

        # 3. Both failed
        return {"statusCode": 401, "verified": False}

    except Exception as e:
        logging.error(f"MFA processing error for {username}: {e}")
        return {"statusCode": 500}


# --- Core Authentication Function ---

def authenticate_user(username: str, password_attempt: str, mfa_code: str):
    """
    Handles the complete authentication logic.
    """
    if not all([username, password_attempt, mfa_code]):
        return 400, {
            "success": False,
            "authenticated": False,
            "error": "Nom d'utilisateur, mot de passe et code 2FA sont requis."
        }

    with get_session() as session:
        # 4. Try to find the corresponding user with the username
        stmt = select(User).where(User.username == username)
        user = session.exec(stmt).first()

        if not user:
            return 404, {
                "success": False,
                "authenticated": False,
                "error": f"L'utilisateur '{username}' n'existe pas ou a été supprimé."
            }

        # 1. & 2. Compare the gendate to today date (6 months validity)
        if user.gendate:
            expiration_date = user.gendate + timedelta(days=180)
            if datetime.now() > expiration_date:
                return 401, {
                    "success": False,
                    "authenticated": False,
                    "expired": True,
                    "expirationDate": expiration_date.isoformat() + "Z",
                    "requiresRenewal": True,
                    "message": "Identifiants expirés, renouvellement nécessaire."
                }

        # 3. & 5. Validate authentication data
        try:
            # Validate password
            decrypted_password = cipher.decrypt(user.password.encode()).decode()
            if decrypted_password != password_attempt:
                # Invalid password, return generic error
                return 401, {
                    "success": False,
                    "authenticated": False,
                    "error": "Identifiants invalides ou code 2FA incorrect."
                }

            # If password is correct, validate MFA
            mfa_result = verify_mfa(username, mfa_code, session)
            if mfa_result.get("statusCode") != 200:
                # Invalid MFA, return generic error
                return 401, {
                    "success": False,
                    "authenticated": False,
                    "error": "Identifiants invalides ou code 2FA incorrect."
                }

            # If both password and MFA are correct
            return 200, {
                "success": True,
                "authenticated": True,
                "userId": user.id,
                "username": user.username,
                "message": "Authentification réussie."
            }

        except Exception as e:
            logging.error(f"Authentication error for user '{username}': {e}")
            return 500, {
                "success": False,
                "authenticated": False,
                "error": "Erreur interne du serveur."
            }


# --- OpenFaaS Handler ---

def handle(event, context):
    """
    Handles the incoming request from OpenFaaS.
    """
    try:
        if not event.body:
            return {"statusCode": 400, "body": {"error": "Request body is empty"}}

        body = json.loads(event.body)
        username = body.get("username")
        password = body.get("password")
        mfa_code = body.get("mfa_code")

        status_code, response_body = authenticate_user(username, password, mfa_code)

        return {
            "statusCode": status_code,
            "body": response_body,
            "headers": {
                "Content-Type": "application/json"
            }
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": {"error": "Invalid JSON format in request body."}
        }
    except Exception as e:
        logging.error(f"Unhandled exception in handler: {e}")
        return {
            "statusCode": 500,
            "body": {
                "success": False,
                "authenticated": False,
                "error": "Erreur interne du serveur."
            }
        }