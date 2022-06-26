import gnupg

from models import ShamirEmail
from shamir.core import encrypt

gpg = gnupg.GPG()
keys = gpg.list_keys()


async def encrypt_email(email: str, user_id: int):
    length = len(keys)
    shares = encrypt(email, length)
    objs = []
    for i in range(length):
        objs.append(ShamirEmail(
            key=str(gpg.encrypt(str(shares[i]), recipients=keys[i]['fingerprint'])),
            encrypted_by=keys[i]['uids'][0],
            user_id=user_id
        ))
    await ShamirEmail.bulk_create(objs)


if __name__ == '__main__':
    pass
