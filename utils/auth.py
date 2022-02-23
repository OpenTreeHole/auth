import base64
import hashlib
import secrets

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from sanic import Sanic

from settings import get_sanic_app

app = Sanic.get_app()


def many_hashes(string: str) -> str:
    iterations = 1
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


def get_private_key(key_file):
    with open(key_file, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def get_public_key(key_file):
    with open(key_file, 'rb') as f:
        return serialization.load_pem_public_key(f.read())


PUBLIC_KEY = get_public_key(app.config.get('EMAIL_PUBLIC_KEY_PATH', 'data/treehole_demo_public.pem'))
PRIVATE_KEY = get_private_key(app.config.get('EMAIL_PRIVATE_KEY_PATH', 'data/treehole_demo_private.pem'))

PADDING = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None
)


def rsa_encrypt(plaintext: str) -> str:
    encrypted_bytes = PUBLIC_KEY.encrypt(plaintext.encode('utf-8'), PADDING)
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def rsa_decrypt(encrypted: str) -> str:
    plain_bytes = PRIVATE_KEY.decrypt(base64.b64decode(encrypted), PADDING)
    return plain_bytes.decode('utf-8')


if __name__ == '__main__':
    app = get_sanic_app()
    print(many_hashes('20300680017@fudan.edu.cn'))
