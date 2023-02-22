"rextlib - Utils"

from __future__ import annotations

__all__ = (
    "make_error_message", "make_simple_error_text", "code_block", "format_text",
    "map_length", "PerformanceStatistics", "take_performance_statistics",
    "make_self_from_row", "camel_to_snake_case", "dict_camel_to_snake_case",
    "CooldownManager"
)

from typing import Self, Generic, TypeVar, ParamSpec, TypedDict, Any
from collections.abc import Callable, Iterator, Iterable, Sized, Hashable

from traceback import TracebackException

from dataclasses import dataclass
from time import time
from re import sub

from concurrent.futures import ThreadPoolExecutor
from asyncio import AbstractEventLoop, all_tasks, get_running_loop

from psutil import cpu_percent, virtual_memory

from .cacher import Cacher, DictCache


@dataclass
class CooldownContext:
    "クールダウンの情報を格納するためのクラスです。"

    count: int = 0
    deadline: float = 0.
CKeyT = TypeVar("CKeyT", bound=Hashable)
class CooldownManager(Generic[CKeyT]):
    "簡単にクールダウンを実装するのに使うクラスです。"

    def __init__(
        self, cacher: Cacher,
        rate: int = 2, per: float = 2.,
        max_cooldown_count: int = 3
    ) -> None:
        self.rate, self.per = rate, per
        self.max_cooldown_count = max_cooldown_count
        self.cache = cacher.register(
            DictCache[CKeyT, CooldownContext](
                self.per * self.max_cooldown_count,
                auto_update_deadline=False
            )
        )

    def get_retry_after(self, key: CKeyT) -> float:
        "何秒後にクールダウンが終わるかを返します。"
        return self.cache[key].deadline - time()

    def check(self, key: CKeyT) -> bool:
        "指定されたキーがクールダウンしていないかどうかをチェックします。"
        if key in self.cache:
            self.cache[key].count += 1
            if self.cache[key].count % self.rate == 0:
                if self.cache[key].count < self.max_cooldown_count:
                    self.cache.update_deadline(self.per * self.cache[key].count, key)
                return False
        else:
            self.cache[key] = CooldownContext()
            self.cache.update_deadline(self.per, key)
        return True


MsfrT = TypeVar("MsfrT")
def make_self_from_row(dataclass: type[MsfrT], row: Iterable[Any]) -> MsfrT:
    """dataclassによるデータクラスのインスタンスを作成します。データベースの列を渡すことを想定しています。
    `dataclass`はその列の型と同じ順番でアノテーションが設定されている必要があります。"""
    return dataclass(**{key: arg for key, arg in zip(dataclass.__annotations__.keys(), row)})


ArReT, ArP = TypeVar("ArReT"), ParamSpec("ArP")
class AsyncFuncIO:
    "同期関数をスレッドプールで非同期に対応させるのに使える関数です。"

    def __init__(self, executor: ThreadPoolExecutor, loop: AbstractEventLoop | None = None) -> None:
        self.executor, self.loop = executor, loop or get_running_loop()

    async def run(
        self, func: Callable[ArP, ArReT],
        *args: ArP.args, **kwargs: ArP.kwargs
    ) -> ArReT:
        "同期関数を非同期に実行します。"
        return await self.loop.run_in_executor(
            self.executor, lambda: func(*args, **kwargs)
        )

    @classmethod
    def from_executors(
        cls, executors: Executors,
        attr_name: str = "normal",
        *args: Any, **kwargs: Any
    ) -> Self:
        "`.Executors`から作ります。"
        return cls(getattr(executors, attr_name) *args, **kwargs)


@dataclass
class Executors(AsyncFuncIO):
    "時間のかかるブロッキングする処理を別スレッドで簡単に行うのに使うExecutorを格納するためのクラスです。"

    normal: ThreadPoolExecutor
    "通常の処理を回す際はこちらを使用してください。Botのclose時にはfutureはキャンセルされます。"
    cleaning: ThreadPoolExecutor
    "お片付け系の実行しないということがない方が良いような処理はこちらでやってください。"

    def __post_init__(self) -> None:
        self.init_super = super().__init__

    @classmethod
    def default(
        cls, prefix: str = "",
        normal_name: str = "normal_executor",
        cleaning_name: str = "cleaning_executor"
    ) -> Self:
        "このクラスのインスタンスを作ります。"
        return cls(*(
            ThreadPoolExecutor(i, thread_name_prefix=prefix)
            for i, prefix in (
                (4, f"{prefix}{normal_name}"),
                (2, f"{prefix}{cleaning_name}")
            )
        ))

    def close(self) -> None:
        "Executorを閉じます。"
        self.normal.shutdown(False, cancel_futures=True)
        self.cleaning.shutdown(True)


def make_error_message(error: BaseException) -> str:
    "渡されたエラーから全文を作ります。"
    return "".join(TracebackException.from_exception(error).format())


def make_simple_error_text(error: BaseException) -> str:
    "渡されたエラーから名前とエラー内容の文字列にします。"
    return f"{error.__class__.__name__}: {error}"


def code_block(code: str, type_: str = "") -> str:
    "渡された文字列をコードブロックで囲みます。"
    return f"```{type_}\n{code}\n```"


def format_text(text: dict[str, str], **kwargs: str) -> dict[str, str]:
    "辞書の全ての値に`.format(**kwargs)`をします。"
    for key in text.keys():
        text[key] = text[key].format(**kwargs)
    return text


KeyT, ValueT = TypeVar("KeyT"), TypeVar("ValueT", bound=Sized)
def map_length(data: dict[KeyT, ValueT]) -> Iterator[tuple[tuple[KeyT, ValueT], int]]:
    "渡された辞書の`.items`で返されるタプルと値の大きさの整数を入れたタプルを返すイテレーターを返します。"
    return map(lambda key: ((key, data[key]), len(data[key])), data.keys())


class PerformanceStatistics(TypedDict):
    "サーバーの動作状況をまとめた辞書の型です。"

    cpu: float
    "CPU使用率"
    memory: tuple[float, float, float]
    "メモリ使用量と未使用量、そして合計の三つが格納されたタプル"
    task_amount: int
    "非同期イベントループのタスクの数です。"
    database_pool_size: int
    "データベースの接続の数。"

def take_performance_statistics(
    loop: AbstractEventLoop | None,
    database_pool_size: int
) -> PerformanceStatistics:
    "現在の動作状況をまとめた辞書を返します。"
    memory = virtual_memory()
    return PerformanceStatistics(
        cpu=cpu_percent(interval=1),
        memory=(
            memory.used,
            memory.free,
            memory.total
        ),
        task_amount=0 if loop is None else len(all_tasks(loop)),
        database_pool_size=database_pool_size
    )


def camel_to_snake_case(key: str, support_upper_camel_case: bool = True) -> str:
    "キャメルケースをスネークケースにします。"
    value = sub("([A-Z])", lambda s: "_%s" % s.group(1).lower(), key)
    if support_upper_camel_case and value and value[0] == "_":
        value = value[1:]
    return value


def dict_camel_to_snake_case(
    data: dict[str, Any], *args: Any,
    replace_values: dict[str, Callable[[Any], Any]] | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    "渡された辞書のキーをキャメルケースからスネークケースにします。"
    return {
        camel_to_snake_case(key, *args, **kwargs):
            replace_values[key](value) # type: ignore
                if key in (replace_values or ())
                else value
        for key, value in data.items()
    }