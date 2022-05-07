# rtlib - Chiper

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

    def decrypt(self, text: str) -> str:
        "復号化します。"
        return self.fernet.decrypt(text.encode()).decode()