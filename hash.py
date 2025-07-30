import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode
import json

def hash_password(password: str) -> bytes:
    salt = os.urandom(16) 
    kdf = Scrypt(
        salt=salt,
        length=32, # Türetilen anahtarın uzunluğu (bytes)
        n=2**14,   # CPU/bellek maliyeti (16384)
        r=8,       # Block size
        p=1,       # Parallelization
        backend=default_backend()
    )
    hashed_password_bytes = kdf.derive(password.encode('utf-8'))
    return urlsafe_b64encode(salt + hashed_password_bytes)

def verify_password(stored_hashed_password: bytes, password_to_check: str) -> bool:
    decoded_stored = urlsafe_b64decode(stored_hashed_password)
    salt = decoded_stored[:16] # İlk 16 byte tuzdur
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    
    try:
        kdf.verify(password_to_check.encode('utf-8'), decoded_stored[16:])
        return True
    except Exception: # InvalidKeyException veya diğer olası hatalar
        return False

def save_hashed_password(file_path: str, hashed_password_with_salt: bytes):
    """Hashlenmiş parolayı (tuz ile birlikte) bir dosyaya kaydeder."""
    with open(file_path, 'wb') as f: # binary modda yaz
        f.write(hashed_password_with_salt)
    print(f"Hashlenmiş parola '{file_path}' dosyasına kaydedildi.")

def load_hashed_password(file_path: str) -> bytes:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Hashlenmiş parola dosyası bulunamadı: {file_path}")
    with open(file_path, 'rb') as f: # binary modda oku
        hashed_password_with_salt = f.read()
    return hashed_password_with_salt