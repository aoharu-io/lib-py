# rextlib - Data Manager

from typing import TypeVar, Self
from collections.abc import AsyncIterator

from inspect import iscoroutinefunction, isasyncgenfunction, getsource, getfile

from warnings import filterwarnings
from dataclasses import dataclass
from functools import wraps

from aiomysql import Pool, Cursor, create_pool

from .config import Databases as DatabasesConfig


filterwarnings('ignore', module=r"aiomysql")
__all__ = ("DatabaseManager", "cursor", "fetchstep", "DatabasePools")
cursor: Cursor
cursor = None # type: ignore


async def fetchstep(
    cursor: Cursor, sql: str,
    args: tuple | None = None,
    cycle: int = 50
) -> AsyncIterator[tuple]:
    "少しずつデータベースからデータを読み込みます。(`LIMIT`が使われます。)"
    now, rows = 0, (1,)
    while rows:
        await cursor.execute(sql.replace(";", f" LIMIT {now}, {cycle};"), args)
        if rows := await cursor.fetchall():
            for row in rows:
                yield row
        now += cycle


CaT = TypeVar("CaT")
class DatabaseManager:
    "データベースを簡単に処理するためのクラスです。"

    pool: Pool
    fetchstep = staticmethod(fetchstep)

    def __init_subclass__(cls) -> None:
        for key, value in list(cls.__dict__.items()):
            if ((gen := isasyncgenfunction(value)) or iscoroutinefunction(value)) \
                    and not getattr(value, "__dm_ignore__", False):
                # `cursor`の引数を増設する。
                l = {}
                source = getsource(value).replace("self",  "self, cursor", 1)
                if_count = int(len(source[:source.find("d")]) / 4) - 1
                source = "{}{}".format(
                    "\n" * (value.__code__.co_firstlineno - if_count - 1), "\n".join((
                    "\n".join(f"{'    '*i}if True:" for i in range(if_count)), source
                )))
                exec(compile(source, getfile(value), "exec"), value.__globals__, l)
                # 新しい関数を作る。
                if gen:
                    @wraps(l[key])
                    async def _new( # type: ignore
                        self: DatabaseManager, *args, __dm_func__=l[key], **kwargs
                    ):
                        if "cursor" in kwargs:
                            async for data in __dm_func__(self, kwargs.pop("cursor"), *args, **kwargs):
                                yield data
                        else:
                            async with self.pool.acquire() as conn:
                                async with conn.cursor() as cursor:
                                    async for data in __dm_func__(self, cursor, *args, **kwargs):
                                        yield data
                else:
                    @wraps(l[key])
                    async def _new(
                        self: DatabaseManager, *args, __dm_func__=l[key], **kwargs
                    ):
                        if "cursor" in kwargs:
                            return await __dm_func__(self, kwargs.pop("cursor"), *args, **kwargs)
                        else:
                            async with self.pool.acquire() as conn:
                                async with conn.cursor() as cursor:
                                    return await __dm_func__(self, cursor, *args, **kwargs)
                setattr(cls, key, _new)

    @staticmethod
    def ignore(func: CaT) -> CaT:
        setattr(func, "__dm_ignore__", True)
        return func


@dataclass
class DatabasePools:
    "データベースのプールを格納するためのクラスです。"

    write: Pool
    read: Pool
    _read_is_write = False

    @classmethod
    async def from_config(cls, config: DatabasesConfig) -> Self:
        "データベースの設定からこのクラスのインスタンスを作ります。"
        self = cls(None, None) # type: ignore
        self.write = await create_pool(**config["write"])
        self._read_is_write = "read" in config
        self.read = await create_pool(
            **config["read"] # type: ignore
        ) if self._read_is_write else self.write
        return self

    def close(self) -> None:
        "プールを閉じます。"
        self.write.close()
        if not self._read_is_write:
            self.read.close()