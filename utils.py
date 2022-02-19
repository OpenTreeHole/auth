import base64
import hashlib
import time

from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
from Crypto.PublicKey import RSA

from server import app


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


if __name__ == '__main__':
    start = time.time()
    many_hashes('hi')
    end = time.time()
    print(end - start)
