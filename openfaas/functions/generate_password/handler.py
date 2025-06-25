import os
import base64
import qrcode
import io
import psycopg2
from cryptography.fernet import Fernet
from datetime import datetime

def handle(event, context):
    # Générer un mot de passe de 24 caractères
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(24))

    # Générer le QR code
    qr = qrcode.make(password)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Chiffrer le mot de passe
    key = os.environ.get('ENCRYPT_KEY')
    f = Fernet(key.encode())
    encrypted_password = f.encrypt(password.encode()).decode()

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
    cur.execute('''INSERT INTO users (username, password, mfa, gendate, expired) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (username) DO UPDATE SET password=EXCLUDED.password, mfa=EXCLUDED.mfa, gendate=EXCLUDED.gendate, expired=FALSE''',
                (username, encrypted_password, '', gendate, False))
    conn.commit()
    cur.close()
    conn.close()
    return {"password": password, "qr": qr_b64} 