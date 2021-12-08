from typing import Generator
import numpy as np
import struct

def take(gen: Generator, n: int = 1):
    return [next(gen) for _ in range(n)]


def RC4_keystream(key: bytes):
    S = np.arange(256, dtype='uint8')
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]

    i = 0
    j = 0
    while True:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        yield S[(int(S[i]) + S[j]) % 256]


def encrypt(rc4_keystream: Generator, plaintext: str):
    result = b''

    for i in range(len(plaintext)):
        result += struct.pack('B', (take(rc4_keystream)
                              [0] ^ ord(plaintext[i])))

    return result

def decrypt(rc4_keystream: Generator, encrypted_text: bytes):
    result = ''
    
    for i in range(len(encrypted_text)):
        result += chr(encrypted_text[i] ^ np.uint8(take(rc4_keystream)[0]))

    return result

if __name__ == '__main__':
    key = 'Key'.encode()
    rc4 = RC4_keystream(key)
    rc4_decrypt = RC4_keystream(key)
    # print(encrypt(rc4, 'Plaintext'))
    print(decrypt(rc4_decrypt, encrypt(rc4, 'Plaintext')))
