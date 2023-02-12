"rextlib - Log"

__all__ = ("set_stream_handler", "set_handler", "set_output_handler")

from typing import Any

from logging.handlers import RotatingFileHandler
import logging

from os import mkdir
from os.path import exists


BASE_FORMAT = "[%(name)s] [%(levelname)s] %(message)s"
NORMAL_FORMATTER = logging.Formatter(BASE_FORMAT)
EXTENDED_FORMATTER = logging.Formatter(f"[%(asctime)s] {BASE_FORMAT}", "%Y-%m-%d %H:%M:%S")


def set_output_handler(logger: logging.Logger, file_name: str = "main") -> None:
    "ファイル出力をロガーに設定します。"
    if not exists("data/logs"):
        mkdir("data/logs")
    handler = RotatingFileHandler(
        filename=f"data/logs/{file_name}", encoding='utf-8',
        mode='w', maxBytes=32 * 1024 * 1024, backupCount=10
    )
    handler.setFormatter(EXTENDED_FORMATTER)
    logger.addHandler(handler)


def set_stream_handler(logger: logging.Logger) -> None:
    "渡されたロガーのログを標準出力に出力するようにします。"
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(NORMAL_FORMATTER)
    logger.addHandler(handler)


def set_handler(
    logger: logging.Logger,
    output_file: bool = True,
    **output_kwargs: Any
) -> None:
    "渡された`Logger`でログを標準出力に出力するようにします。オプションでファイル出力します。"
    set_stream_handler(logger)
    if output_file:
        set_output_handler(logger, **output_kwargs)