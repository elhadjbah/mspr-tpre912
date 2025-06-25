import os
import base64
import qrcode
import io
import pyotp
import psycopg2
from cryptography.fernet import Fernet
from datetime import datetime

def handle(event, context):
    # Générer un secret TOTP
    secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=event.get('username', 'user'), issuer_name="COFRAP")

    # Générer le QR code
    qr = qrcode.make(totp_uri)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Chiffrer le secret
    key = os.environ.get('ENCRYPT_KEY')
    f = Fernet(key.encode())
    encrypted_secret = f.encrypt(secret.encode()).decode()

    # Stocker en base
    conn = psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
        port=os.environ.get('POSTGRES_PORT', 5432)
    )
    cur = conn.cursor()
    username = event.get('username', 'user')
    gendate = datetime.utcnow()
    cur.execute('''INSERT INTO users (username, password, mfa, gendate, expired) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (username) DO UPDATE SET mfa=EXCLUDED.mfa, gendate=EXCLUDED.gendate, expired=FALSE''',
                (username, '', encrypted_secret, gendate, False))
    conn.commit()
    cur.close()
    conn.close()
    return {"secret": secret, "qr": qr_b64} 