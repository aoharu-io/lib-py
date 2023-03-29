"rextlib - Log"

__all__ = ("set_stream_handler", "set_handler", "set_file_handler")

from typing import Any

from logging.handlers import RotatingFileHandler
import logging

from pathlib import PurePath

from os import mkdir
from os.path import exists


BASE_FORMAT = "[%(name)s] [%(levelname)s] %(message)s"
NORMAL_FORMATTER = logging.Formatter(BASE_FORMAT)
EXTENDED_FORMATTER = logging.Formatter(f"[%(asctime)s] {BASE_FORMAT}", "%Y-%m-%d %H:%M:%S")


_last_added_file_handler = None
def set_file_handler(
    logger: logging.Logger,
    file_path: str | PurePath = "main.log",
    **kwargs: Any
) -> None:
    "ファイル出力をロガーに設定します。"
    if isinstance(file_path, str):
        file_path = PurePath(file_path)
    if not exists(file_path.parent):
        mkdir(file_path.parent)

    kwargs.setdefault("filename", file_path)
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("mode", "w")
    kwargs.setdefault("maxBytes", 32 * 1024 * 1024)
    kwargs.setdefault("backupCount", 10)

    handler = RotatingFileHandler(**kwargs)
    handler.setFormatter(EXTENDED_FORMATTER)

    # 過去に追加したハンドラがあるのなら、それを削除する。
    global _last_added_file_handler
    if _last_added_file_handler is not None and \
            _last_added_file_handler in logger.handlers:
        logger.removeHandler(_last_added_file_handler)

    logger.addHandler(handler)
    _last_added_file_handler = handler


def set_stream_handler(logger: logging.Logger) -> None:
    "渡されたロガーのログを標準出力に出力するようにします。"
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(NORMAL_FORMATTER)
    logger.addHandler(handler)


def set_handler(
    logger: logging.Logger,
    output_file: bool = True,
    stream: bool = True,
    **output_kwargs: Any
) -> None:
    "渡された`Logger`でログを標準出力に出力するようにします。また、ファイル出力もします。"
    if stream:
        set_stream_handler(logger)
    if output_file:
        set_file_handler(logger, **output_kwargs)