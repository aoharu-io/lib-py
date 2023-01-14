# rextlib - Data Manager

from typing import TypeVar, Self, Any
from collections.abc import AsyncIterator, Callable

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
) -> AsyncIterator[Any]:
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

    db: Pool
    fetchstep = staticmethod(fetchstep)

    def __init_subclass__(cls) -> None:
        for key, value in list(cls.__dict__.items()):
            if ((gen := isasyncgenfunction(value)) or iscoroutinefunction(value)) \
                    and not getattr(value, "__dm_ignore__", False):
                # `cursor`の引数を増設する。
                l = {}
                source = getsource(value).replace("self",  "self, cursor", 1)
                index = source.find("@")
                if index == -1:
                    index = source.find("async def ")

                if_count = int(index / 4)
                source = "{}{}".format(
                    "\n" * (value.__code__.co_firstlineno - if_count - 1), "\n".join((
                    "\n".join(f"{'    '*i}if True:" for i in range(if_count)), source
                )))
                exec(compile(source, getfile(value), "exec"), value.__globals__, l)

                # 新しい関数を作る。
                cursors = getattr(value, "__dm_cursor_classes__") if \
                    hasattr(value, "__dm_cursor_classes__") else ()
                if gen:
                    @wraps(l[key])
                    async def _new( # type: ignore
                        self: DatabaseManager, *args,
                        __dm_func__=l[key],
                        __dm_cursors__=cursors,
                        **kwargs
                    ):
                        if "cursor" in kwargs:
                            async for data in __dm_func__(
                                self, kwargs.pop("cursor"),
                                *args, **kwargs
                            ):
                                yield data
                        else:
                            async with self.db.acquire() as conn:
                                async with conn.cursor(*__dm_cursors__) as cursor:
                                    async for data in __dm_func__(
                                        self, cursor, *args, **kwargs
                                    ):
                                        yield data
                else:
                    @wraps(l[key])
                    async def _new(
                        self: DatabaseManager, *args,
                        __dm_func__=l[key],
                        __dm_cursors__=cursors,
                        **kwargs
                    ):
                        if "cursor" in kwargs:
                            return await __dm_func__(
                                self, kwargs.pop("cursor"),
                                *args, **kwargs
                            )
                        else:
                            async with self.db.acquire() as conn:
                                async with conn.cursor(*__dm_cursors__) as cursor:
                                    return await __dm_func__(self, cursor, *args, **kwargs)
                setattr(cls, key, _new)

    @staticmethod
    def set_to_ignore(func: CaT) -> CaT:
        "メソッドをデータベース使わない関数とするデコレータです。"
        setattr(func, "__dm_ignore__", True)
        return func

    @staticmethod
    def set_cursor_cls(*cursor_clses: type[Cursor]) -> Callable[[CaT], CaT]:
        "カーソルのクラスを変更するためのデコレータです。"
        def decorator(func: CaT) -> CaT:
            setattr(func, "__dm_cursor_classes__", cursor_clses)
            return func
        return decorator


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