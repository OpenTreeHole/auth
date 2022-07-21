import secrets
from typing import List
import sys, scipy.linalg
import numpy as np
from Crypto.Random import random

MAX_LENGTH = 64

"""
Mainly from <https://github.com/cxjdavin/thresholdsecretsharing/blob/master/blakley.py>.
"""
class BlakleySSS:
    @staticmethod
    def split_key(key, n, k):
        # Generate x vector
        x = [int.from_bytes(key, byteorder=sys.byteorder)]
        for i in range(k - 1):
            x.append(random.randint(0, 2 ** (MAX_LENGTH * 8)))
        x = np.array(x)

        # Generate Pascal Matrix
        A = np.ones((n, k)).astype(int)
        for r in range(1, n):
            for c in range(1, k):
                A[r, c] = A[r, c - 1] + A[r - 1, c]

        # Generate y vector, where Ax = y
        y = np.dot(A, x)

        # Split keys
        keys = [A[i].tolist() + [y[i]] for i in range(n)]

        # Return keys
        return keys

    @staticmethod
    def combine_keys(keys):

        k = len(keys[0]) - 1
        if k > len(keys):
            raise Exception(
                "Insufficient keys provided for decryption. Please ensure the first {} keys are valid.".format(k))

        # Generate matrix and y vector from keys, filter for first k keys
        B = np.matrix([keys[i][:-1] for i in range(k)])[:k]
        y = np.array([keys[i][-1] for i in range(k)])[:k]

        if np.linalg.matrix_rank(B) != k:
            raise Exception(
                "Keys provided are not linearly independent. Please ensure the first {} keys are valid.".format(k))

        # Solve simultaneous equation: Bx = y
        #
        # Implementation notes:
        # Problem 1:    Currently, no math packages can solve linear system of equations with arbitrary length numbers
        #               But, y is made up of values that are up to 256 bits long
        # Workaround:   Since elements in B is invertible, find B^-1 (invB)
        #               Use scipy since numpy doesn't have in-built inv function
        # Problem 2:    invB may contain fractions
        # Workaround 2: Since elements in B are integers, det(B) is an integer.
        #               Using invB = adj(B)/det(B) definition, defer division by det(B) till after multiplying with y
        invB = scipy.linalg.inv(B)
        detB = round(scipy.linalg.det(B))

        # Secret S = AES key = invA[0] * y (since we only care about x[0])
        #
        # Implementation notes:
        # type(round(detB * invB[0][0]))        -> float64
        # type(int(round(detB * invB[0][0])))   -> native Python int
        # type(round(detB))                     -> native Python int
        # Need to use // instead of / to maintain numerical precision
        S = sum(int(round(detB * invB[0][i])) * y[i] for i in range(k)) // round(detB)
        key = S.to_bytes(MAX_LENGTH, byteorder=sys.byteorder)

        # Return key
        return key


def encrypt(secret: str, num: int = 7, threshold: int = 0) -> List[str]:
    if len(secret) > MAX_LENGTH:
        raise ValueError(f'length of secret should less than {MAX_LENGTH}')
    if threshold == 0:
        threshold = num // 2 + 1
    elif threshold > num:
        raise ValueError('threshold is bigger than num, secret could not be recovered')
    return list(map(lambda x: str(x), BlakleySSS.split_key(secret.encode(), num, threshold)))


def decrypt(share: List) -> str:
    keys = [[int(num) for num in key[1:-1].replace(' ', '').split(',')] for key in share]
    return (BlakleySSS.combine_keys(keys)).decode()


if __name__ == '__main__':
    print(decrypt(encrypt('saxasxasxlassedhvcudsasxaaxasxasxasxasqwqweq1212xasxasxasxhcisdc')[2:6]))
