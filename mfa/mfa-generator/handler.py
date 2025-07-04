import hashlib
import os
import random
import qrcode
import base64
import json
import onetimepass as otp
from io import BytesIO
from typing import Optional
from cryptography.fernet import Fernet
from sqlmodel import SQLModel, Field, create_engine, Session, select
import logging
from datetime import datetime

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
DATABASE_URL = os.getenv("DATABASE_URL", "")
logging.debug(f"\nDATABASE_URL : {DATABASE_URL}")

# Connection pool settings optimized for serverless
engine = create_engine(
    DATABASE_URL
)

logging.debug(f"\nENGINE : {engine}")


def get_session():
    """Get database session - use this pattern in serverless functions"""
    return Session(engine)

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

# --- Assume User model (as defined above) and other config is present ---
# ...

def generate_mfa():
    """
    Generates all necessary MFA data without persisting it.
    This function remains the same as its job is only to generate the data.
    """
    secret_bytes = os.urandom(20)
    secret = base64.b32encode(secret_bytes).decode('utf-8')
    otp_int = otp.get_hotp(secret=secret.encode('utf-8'), intervals_no=0)
    initial_otp = f"{otp_int:06d}"

    img = qrcode.make(initial_otp)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    backup_codes = [str(random.randint(100000, 999999)) for _ in range(6)]

    return {
        "otp": initial_otp,
        "secret": secret,
        "qrCode": f"data:image/png;base64,{qr_code_base64}",
        "backupCodes": backup_codes,
    }


def persist_mfa(username: str, mfa_setup_data: dict):
    """
    Persists all generated MFA data (secret, counter, and hashed backup codes)
    into a single encrypted field for a user.
    """
    if not username or username is None:
        return {
            "statusCode": 400,
            "body": {"message": "username is invalid, null or empty string"},
        }
    with get_session() as session:
        stmt = select(User).where(User.username == username)
        user = session.exec(stmt).first()

        if not user:
            return {
                "statusCode": 404,
                "body": {"message": "user does not exit please create the corresponding user first"},
            }

        # Hash the backup codes for secure storage.
        hashed_backup_codes = [hashlib.sha256(code.encode()).hexdigest() for code in mfa_setup_data["backupCodes"]]

        # Combine ALL mfa data into one object for encryption.
        mfa_to_encrypt = {
            "secret": mfa_setup_data["secret"],
            "counter": 0,
            "backup_codes_hashed": hashed_backup_codes # Add hashed codes here
        }
        encrypted_mfa_blob = cipher.encrypt(json.dumps(mfa_to_encrypt).encode()).decode()

        # Update the single 'mfa' field on the user record.
        user.mfa = encrypted_mfa_blob
        session.commit()
        session.refresh(user)

        # The response body remains the same, returning the necessary plaintext data to the user.
        response_body = {
            "success": True,
            "userId": user.id,
            "secret": mfa_setup_data["secret"],
            "qrCode": mfa_setup_data["qrCode"],
            "backupCodes": mfa_setup_data["backupCodes"],
            "encryptedSecret": encrypted_mfa_blob,
            "message": "Secret 2FA généré avec succès",
        }

        return {"statusCode": 200, "body": response_body}


def verify_mfa(username: str, otp_code: str):
    """
    Verifies an HOTP code or a backup code from the single encrypted MFA blob.
    """
    with get_session() as session:
        stmt = select(User).where(User.username == username)
        user = session.exec(stmt).first()

        if not user or not user.mfa:
            return {"statusCode": 404, "body": {"message": "User not found or MFA not configured."}}

        try:
            # Decrypt the single blob to get all MFA data
            decrypted_mfa_json = cipher.decrypt(user.mfa.encode()).decode()
            mfa_data = json.loads(decrypted_mfa_json)

            # 1. Attempt to verify as a primary HOTP code
            is_hotp_valid = otp.valid_hotp(
                token=otp_code,
                secret=mfa_data["secret"].encode('utf-8'),
                last_counter=mfa_data["counter"]
            )

            if is_hotp_valid:
                mfa_data['counter'] += 1
                # Re-encrypt the entire updated blob and save it
                user.mfa = cipher.encrypt(json.dumps(mfa_data).encode()).decode()
                session.commit()
                return {"statusCode": 200, "body": {"verified": True, "message": "MFA verification successful."}}

            # 2. If HOTP fails, attempt to verify as a backup code
            hashed_backup_codes = mfa_data.get("backup_codes_hashed", [])
            hashed_otp = hashlib.sha256(otp_code.encode()).hexdigest()

            if hashed_otp in hashed_backup_codes:
                # Invalidate the used backup code
                mfa_data['backup_codes_hashed'].remove(hashed_otp)
                # Re-encrypt the entire updated blob and save it
                user.mfa = cipher.encrypt(json.dumps(mfa_data).encode()).decode()
                session.commit()
                return {"statusCode": 200, "body": {"verified": True, "message": "Backup code verification successful."}}

            # 3. If both fail
            return {"statusCode": 401, "body": {"verified": False, "message": "Invalid OTP or backup code."}}

        except Exception as e:
            logging.error(f"MFA processing error for {username}: {e}")
            return {"statusCode": 500, "body": {"message": "Internal MFA processing error."}}

def handle(event, context):
    try:
        body = json.loads(event.body)
        print(f"\nSTART : {body}")
        logging.debug(f"\nSTART : {body}")
        username = body.get("username")
        response = persist_mfa(username, generate_mfa())
        return response

    except Exception as e:
        print(f"\nSTART : {e} {event.body}")
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }