__all__ = ("Database", "Databases")

from typing import TypedDict, NotRequired


class Database(TypedDict, total=False):
    "データベースの設定の辞書の型です。"

    host: str
    user: str
    password: str
    db: str
    port: int
    maxsize: int
    minsize: int


class Databases(TypedDict):
    "データベースの設定の型です。"

    read: NotRequired[Database]
    """読み込み専用のデータベースです。
    省略時は`.write`と同じ物が使われます。
    読み書きが多いサービスの本番時には、ロードバンサを挟みデータベースを分散して、読み込み専用のデータベースを複数用意し、この設定項目を設定しましょう。"""
    write: Database
    "書き込み専用のデータベースです。"