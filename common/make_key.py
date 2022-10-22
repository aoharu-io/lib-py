# rextlib Key

from cryptography.fernet import Fernet


with open("secret.key", "wb") as f:
    f.write(Fernet.generate_key())