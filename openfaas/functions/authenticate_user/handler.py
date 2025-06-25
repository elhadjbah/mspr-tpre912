import os
import psycopg2
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import pyotp

def handle(event, context):
    username = event.get('username')
    password = event.get('password')
    mfa_code = event.get('mfa_code')
    if not username or not password or not mfa_code:
        return {"error": "Missing credentials"}

    conn = psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
        port=os.environ.get('POSTGRES_PORT', 5432)
    )
    cur = conn.cursor()
    cur.execute('SELECT password, mfa, gendate, expired FROM users WHERE username=%s', (username,))
    row = cur.fetchone()
    if not row:
        return {"error": "User not found"}
    enc_password, enc_mfa, gendate, expired = row
    key = os.environ.get('ENCRYPT_KEY')
    f = Fernet(key.encode())
    try:
        dec_password = f.decrypt(enc_password.encode()).decode()
        dec_mfa = f.decrypt(enc_mfa.encode()).decode()
    except Exception:
        return {"error": "Decryption failed"}
    # Vérification mot de passe
    if password != dec_password:
        return {"error": "Invalid password"}
    # Vérification TOTP
    totp = pyotp.TOTP(dec_mfa)
    if not totp.verify(mfa_code):
        return {"error": "Invalid 2FA code"}
    # Vérification date
    now = datetime.utcnow()
    if gendate < now - timedelta(days=180):
        cur.execute('UPDATE users SET expired=TRUE WHERE username=%s', (username,))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": "Account expired"}
    cur.close()
    conn.close()
    return {"success": True} 