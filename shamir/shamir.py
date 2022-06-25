import secrets

import numpy as np


def lagrange(x: np.ndarray, y: np.ndarray) -> int:
    """
    计算拉格朗日插值的常数项 a0
    Args:
        x: x_i 向量
        y: y_i 向量

    Returns:
        拉格朗日插值的常数项 a0
    """
    if len(x) != len(y):
        raise ValueError('x must be the same length as y')
    s = 0
    for i in range(len(y)):
        pi = 1
        for j in range(len(y)):
            if i == j:
                continue
            pi *= - x[j] / (x[i] - x[j])
        s += y[i] * pi
    s = round(s)
    return s


def generate(secret: int, num: int, threshold: int) -> np.ndarray:
    coefficient = np.zeros(threshold)
    coefficient[0] = secret
    for i in range(threshold - 1):
        coefficient[i + 1] = secrets.randbelow(1145141919810)
    vander = np.vander(np.arange(1, num + 1), threshold, increasing=True)
    return vander.dot(coefficient)


def encrypt(secret: str, num: int = 7, threshold: int = 0) -> np.ndarray:
    secret = int.from_bytes(secret.encode(), byteorder='little')
    if threshold == 0:
        threshold = num // 2 + 1
    return generate(secret, num, threshold)


def decrypt(x: np.ndarray, y: np.ndarray) -> str:
    return lagrange(x, y).to_bytes(length=30, byteorder='little').decode().replace('\x00', '')


if __name__ == '__main__':
    print(lagrange([1, 2, 3, 4, 5, 6, 7], generate(123456789, 7, 4)))
