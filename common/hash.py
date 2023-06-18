__all__ = ("get_hash", "get_file_hash")

from hashlib import sha256


def get_hash(data: bytes) -> str:
    "渡されたデータのハッシュを取得します。"
    return sha256(data).hexdigest()


def get_file_hash(file_path: str) -> str:
    "ファイルのハッシュを取得します。"
    with open(file_path, "rb") as f:
        return get_hash(f.read())