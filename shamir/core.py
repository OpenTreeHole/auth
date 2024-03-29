import argparse
import secrets

# the 13th Mersenne prime
P = 2 ** 521 - 1
MAX_LENGTH = 64


class Share:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __str__(self):
        return f'{self.x}\n{self.y}'


Shares = list[Share]


def modular_multiplicative_inverse(x: int, p: int = P) -> int:
    """
    division in integers modulus p means finding the inverse of the denominator
    modulo p and then multiplying the numerator by this inverse
    (Note: inverse of A is B such that A*B % p == 1)
    this can be computed via extended euclidean algorithm
    https://en.wikipedia.org/wiki/Modular_multiplicative_inverse#Computation
    """

    def extended_gcd(a: int, b: int) -> (int, int):
        x = 0
        last_x = 1
        y = 1
        last_y = 0
        while b != 0:
            quot = a // b
            a, b = b, a % b
            x, last_x = last_x - quot * x, x
            y, last_y = last_y - quot * y, y
        return last_x, last_y

    x, _ = extended_gcd(x, p)
    return x


def lagrange(shares: Shares) -> int:
    """
    计算拉格朗日插值的常数项 a0
    """
    x = [i.x for i in shares]
    length = len(shares)
    s = 0
    for i in range(length):
        pi = 1
        for j in range(length):
            if i == j:
                continue
            pi *= x[j] * modular_multiplicative_inverse(x[j] - x[i]) % P
        s = (s + shares[i].y * pi) % P
    return s


def generate(secret: int, num: int, threshold: int) -> Shares:
    def evaluate(coefficient: list[int], x: int) -> int:
        acc = 0
        power = 1
        for c in coefficient:
            acc = (acc + c * power) % P
            power *= x % P
        return acc

    coefficient = [secret] + [secrets.randbelow(P) for i in range(threshold - 1)]
    shares = []
    for i in range(num):
        x = secrets.randbelow(P)
        shares.append(Share(x=x, y=evaluate(coefficient, x)))
    return shares


def encrypt(secret: str, num: int = 7, threshold: int = 0) -> Shares:
    if len(secret) > MAX_LENGTH:
        raise ValueError(f'length of secret should less than {MAX_LENGTH}')
    secret = int.from_bytes(secret.encode(), byteorder='little')
    if secret >= P:
        raise ValueError(f'secret should not bigger than P = {P}')
    if threshold == 0:
        threshold = num // 2 + 1
    elif threshold > num:
        raise ValueError('threshold is bigger than num, secret could not be recovered')
    return generate(secret, num, threshold)


def decrypt(share: Shares) -> str:
    return lagrange(share).to_bytes(length=MAX_LENGTH, byteorder='little').decode().replace('\x00', '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='shamir secret sharing encryption and decryption')
    parser.add_argument('--decrypt', '-d', type=str,
                        help='decrypt from a file of key shares')
    parser.add_argument('--encrypt', '-e', type=str,
                        help='encrypt a given string')
    args = parser.parse_args()

    if args.decrypt:
        with open(args.decrypt, encoding='utf-8') as f:
            lines = f.readlines()
        shares = []
        for i in range(len(lines) // 2):
            shares.append(Share(x=int(lines[i * 2]), y=int(lines[i * 2 + 1])))
        print(decrypt(shares))
    if args.encrypt:
        print(encrypt(args.encrypt))
