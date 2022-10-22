# rextlib - Chiper

from __future__ import annotations

from cryptography.fernet import Fernet

from aiofiles import open as aioopen


__all__ = ("ChiperManager",)


class ChiperManager:
    "暗号を作るためのクラスです。"

    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    @classmethod
    def from_key_file(cls, file_path: str) -> ChiperManager:
        with open(file_path, "rb") as f:
            return cls(f.read())

    @classmethod
    async def from_key_file_async(cls, file_path: str) -> ChiperManager:
        async with aioopen(file_path, "rb") as f:
            return cls(await f.read())

    def encrypt(self, text: str) -> str:
        "暗号化します。"
        return self.fernet.encrypt(text.encode()).decode()

    def encrypt_bytes_to_str(self, text: bytes) -> str:
        "bytesを暗号化してstrにします。"
        return self.fernet.encrypt(text).decode()

    def encrypt_str_to_bytes(self, text: str) -> bytes:
        "strを暗号化してbytesにします。"
        return self.fernet.encrypt(text.encode())

    def decrypt(self, text: str) -> str:
        "復号化します。"
        return self.fernet.decrypt(text.encode()).decode()

    def decrypt_str_to_bytes(self, text: str) -> bytes:
        "strを復号化してbytesにします。"
        return self.fernet.decrypt(text.encode())

    def decrypt_bytes_to_str(self, text: bytes) -> str:
        "bytesを復号化してstrにします。"
        return self.fernet.decrypt(text).decode()