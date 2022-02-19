import base64
import hashlib
import secrets
import time

from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
from Crypto.PublicKey import RSA
from sanic import Sanic

app = Sanic.get_app()


def get_key(key_file):
    with open(key_file) as f:
        data = f.read()
    return PKCS1_cipher.new(RSA.importKey(data))


PUBLIC_KEY = get_key(app.config.get('EMAIL_PUBLIC_KEY_PATH', 'data/treehole_demo_public.pem'))
PRIVATE_KEY = get_key(app.config.get('EMAIL_PRIVATE_KEY_PATH', 'data/treehole_demo_private.pem'))


def encrypt_email(plaintext: str) -> str:
    encrypted_bytes = PUBLIC_KEY.encrypt(bytes(plaintext.encode('utf-8')))
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def decrypt_email(encrypted: str) -> str:
    back_text = PRIVATE_KEY.decrypt(base64.b64decode(encrypted), 0)
    return back_text.decode('utf-8')


def many_hashes(string: str) -> str:
    iterations = 10 ** 6
    byte_string = bytes(string.encode('utf-8'))
    return hashlib.pbkdf2_hmac('sha3_512', byte_string, b'', iterations).hex()


def password_hash(algorithm: str, raw_password: str, salt: str, iterations: int) -> str:
    return base64.b64encode(
        hashlib.pbkdf2_hmac(algorithm, raw_password.encode(), salt.encode(), iterations)
    ).decode()


def make_password(raw_password: str) -> str:
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    algorithm = 'sha256'
    iterations = 216000
    salt: str = ''.join(secrets.choice(chars) for i in range(12))
    hash_b64: str = password_hash(algorithm, raw_password, salt, iterations)
    return f'pbkdf2_{algorithm}${iterations}${salt}${hash_b64}'


def check_password(raw_password: str, encrypted_password: str) -> bool:
    algorithm, iterations, salt, hash_b64 = encrypted_password.split('$')
    algorithm = algorithm.split('_')[-1]
    iterations = int(iterations)
    return password_hash(algorithm, raw_password, salt, iterations) == hash_b64


if __name__ == '__main__':
    start = time.time()
    many_hashes('hi')
    end = time.time()
    print(end - start)
