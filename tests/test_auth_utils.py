from app import app
from utils.auth import rsa_encrypt, rsa_decrypt, make_password, check_password, many_hashes, create_token, verify_token

print(app)


def test_rsa_encrypt():
    plain_text = 'plain text'
    encrypted = rsa_encrypt(plain_text)
    decrypted = rsa_decrypt(encrypted)
    assert len(encrypted) <= 1000
    assert decrypted == plain_text


def test_password():
    password = 'password'
    encrypted = make_password(password)
    assert len(encrypted) <= 128
    assert check_password(password, encrypted) is True


def test_hash():
    identifier = many_hashes('email')
    assert len(identifier) <= 128


def test_jwt():
    access, refresh = create_token(1)
    assert len(access) <= 2000
    assert len(refresh) <= 2000
    assert isinstance(verify_token(access, token_type='access'), dict)
    assert isinstance(verify_token(refresh, token_type='refresh'), dict)
