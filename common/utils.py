# rextlib - Utils

from typing import Self, TypeVar, TypedDict, Any
from collections.abc import Callable, Iterator, Sized

from traceback import TracebackException
from dataclasses import dataclass

from concurrent.futures import ThreadPoolExecutor
from asyncio import AbstractEventLoop, all_tasks

from psutil import cpu_percent, virtual_memory


__all__ = (
    "make_error_message", "make_simple_error_text", "code_block",
    "to_dict_for_dataclass", "format_text", "map_length",
    "PerformanceStatistics", "take_performance_statistics"
)


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


to_dict_for_dataclass: Callable[..., dict[str, Any]] = lambda self: {
    key: getattr(self, key) for key in self.__class__.__annotations__.keys()
}
"データクラスのデータを辞書として出力する`to_dict`を作成します。"


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