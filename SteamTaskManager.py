import argparse
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class Encrypter:
    def __init__(self, password):
        self.password = password.encode('utf-8')
        self.salt = b'\x01\x23\x45\x67\x89\xab\xcd\xef'
        self.iterations = 100000
        self.key_length = 32  # 256 bits
        self.iv_length = 16  # AES block size
        self.backend = default_backend()

    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            iterations=self.iterations,
            salt=self.salt,
            length=self.key_length,
            backend=self.backend
        )
        return kdf.derive(self.password)

    def encrypt_image(self, image_path):
        try:
            with open(image_path, 'rb') as image_file:
                original_image = image_file.read()

            key = self._derive_key()
            iv = key[:self.iv_length]
            cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=self.backend)
            encryptor = cipher.encryptor()
            encrypted_image = encryptor.update(original_image) + encryptor.finalize()

            encrypted_path = image_path.replace(".", "_encrypted.")
            with open(encrypted_path, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_image)

            print("Encryption successful.")
        except Exception as e:
            print("Encryption failed:", e)

    def decrypt_image(self, encrypted_image_path):
        try:
            with open(encrypted_image_path, 'rb') as encrypted_file:
                encrypted_image = encrypted_file.read()

            key = self._derive_key()
            iv = key[:self.iv_length]
            cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            decrypted_image = decryptor.update(encrypted_image) + decryptor.finalize()

            decrypted_path = encrypted_image_path.replace("_encrypted.", "_decrypted.")
            with open(decrypted_path, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_image)

            print("Decryption successful.")
        except Exception as e:
            print("Decryption failed:", e)


def main():
    parser = argparse.ArgumentParser(description="", epilog="For more information and updates, visit: https://github.com/BaptistSec")
    parser.add_argument("action", choices=["encrypt", "decrypt"], help="Action to perform: encrypt or decrypt")
    parser.add_argument("image_path", help="Path to the image file")

    args = parser.parse_args()

    password = input("Enter password: ")
    encrypter = Encrypter(password)

    if args.action == "encrypt":
        encrypter.encrypt_image(args.image_path)
    elif args.action == "decrypt":
        encrypter.decrypt_image(args.image_path)


if __name__ == "__main__":
    main()
