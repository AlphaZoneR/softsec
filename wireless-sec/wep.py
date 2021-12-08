from struct import pack
from numpy import byte
from rc4 import RC4_keystream, encrypt, decrypt
from dataclasses import dataclass

import zlib
import random

@dataclass
class WepPacket:
    initialization_vector: bytes
    cypher_text: bytes
    crc: bytes


if __name__ == '__main__':
    KEY = 'password'.encode()

    key = input('Enter password: ')
    # Clients sends authentication request to server
    # Server sends cleartext challange
    cleartext = 'challange'

    # Client encrypts cleartext using key
    encrypted_cleartext = encrypt(RC4_keystream(key.encode()), cleartext)

    # Client sends encrypted cleartext to server
    # Server decrypts and verifies that the decrypted cypher text is valid
    if decrypt(RC4_keystream(KEY), encrypted_cleartext) != cleartext:
        print("Cleartext challenge failed, disconnecting")
        exit()
    
    print("[Server] Cleartext challenge successful, begin communication")

    message = input('[Client] Send something to the server: ')

    while 'close' not in  message.lower():
        iv = random.randbytes(3)
        iv_key = iv + key.encode()
        cypher_text = encrypt(RC4_keystream(iv_key), message)
        crc = zlib.crc32(message.encode()) % 0xffffffff

        packet = WepPacket(iv, cypher_text, crc)

        print(f'[Client] Sending {packet}')
        print(f'[Server] Received ... {packet}')
        
        server_key = packet.initialization_vector + KEY
        received_message = decrypt(RC4_keystream(server_key), packet.cypher_text)
        if (zlib.crc32(received_message.encode()) == packet.crc):
            print(f'[Server] CRC OK, Received message: {received_message}')
        else:
            print('[Server] The server received a message with modified contents: Invalid CRC')
        message = input('[Client] Send something to the server: ')

