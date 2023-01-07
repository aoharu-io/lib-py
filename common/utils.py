# rextlib - Utils

from typing import Self, TypeVar, TypedDict, Any
from collections.abc import Iterator, Iterable, Sized

from traceback import TracebackException

from dataclasses import dataclass
from re import sub

from concurrent.futures import ThreadPoolExecutor
from asyncio import AbstractEventLoop, all_tasks

from psutil import cpu_percent, virtual_memory


__all__ = (
    "make_error_message", "make_simple_error_text", "code_block", "format_text",
    "map_length", "PerformanceStatistics", "take_performance_statistics",
    "make_self_from_row", "camel_to_snake_case", "dict_camel_to_snake_case"
)


MsfrT = TypeVar("MsfrT")
def make_self_from_row(dataclass: type[MsfrT], row: Iterable[Any]) -> MsfrT:
    """dataclassによるデータクラスのインスタンスを作成します。データベースの列を渡すことを想定しています。
    `dataclass`はその列の型と同じ順番でアノテーションが設定されている必要があります。"""
    return dataclass(**{key: arg for key, arg in zip(dataclass.__annotations__.keys(), row)})


@dataclass
class Executors:
    "時間のかかるブロッキングする処理を別スレッドで簡単に行うのに使うExecutorを格納するためのクラスです。"

    normal: ThreadPoolExecutor
    "通常の処理を回す際はこちらを使用してください。Botのclose時にはfutureはキャンセルされます。"
    clean: ThreadPoolExecutor
    "お片付け系の実行しないということがない方が良いような処理はこちらでやってください。"

    @classmethod
    def default(cls) -> Self:
        "このクラスのインスタンスを作ります。"
        return cls(*(
            ThreadPoolExecutor(i, thread_name_prefix=prefix)
            for i, prefix in ((4, "RT.NormalExecutor"), (2, "RT.CleanExecutor"))
        ))

    def close(self) -> None:
        "Executorを閉じます。"
        self.normal.shutdown(False, cancel_futures=True)
        self.clean.shutdown(True)


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


DcscT = TypeVar("DcscT")
def dict_camel_to_snake_case(
    data: dict[str, DcscT],
    *args: Any, **kwargs: Any
) -> dict[str, DcscT]:
    "渡された辞書のキーをキャメルケースからスネークケースにします。"
    return {
        camel_to_snake_case(key, *args, **kwargs): value
        for key, value in data.items()
    }