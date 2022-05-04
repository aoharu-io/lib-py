# RT - Short URL DataManager

from aiomysql import Pool

from .database import DatabaseManager, cursor


__all__ = ("ShortURLManager",)


class ShortURLManager(DatabaseManager):

    MAX_URL = 150

    def __init__(self, pool: Pool):
        self.pool = pool

    async def prepare_table(self) -> None:
        "テーブルを用意します。"
        await cursor.execute(
            "CREATE TABLE IF NOT EXISTS ShortURL (UserId BIGINT, Url TEXT, Endpoint TEXT);"
        )

    async def read(self, user_id: int, **_) -> list[tuple[str, str]]:
        "データを読み込みます。"
        await cursor.execute(
            "SELECT Url, Endpoint FROM ShortURL WHERE UserId = %s;",
            (user_id,)
        )
        return await cursor.fetchall()

    async def register(self, user_id: int, url: str, endpoint: str) -> None:
        "短縮URLを登録します。"
        assert self.MAX_URL < len(await self.read(user_id, cursor=cursor)), "設定しすぎです。"
        await cursor.execute(
            "SELECT Url FROM ShortURL WHERE Endpoint = %s;", (endpoint,)
        )
        assert not await cursor.fetchone(), "既にそのエンドポイントは使用されています。"
        await cursor.execute(
            "INSERT INTO ShortURL VALUES (%s, %s, %s);",
            (user_id, url, endpoint)
        )

    async def delete(self, user_id: int, endpoint: str) -> None:
        "短縮URLを削除します。"
        await cursor.execute(
            "DELETE FROM ShortURL WHERE UserId = %s AND Endpoint = %s;",
            (user_id, endpoint)
        )