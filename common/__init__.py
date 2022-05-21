# rtlib - Main

import logging

from orjson import dumps as odumps

from . import utils


__all__ = ("utils", "set_handler", "dumps")


def set_handler(logger: logging.Logger) -> None:
    "渡された`Logger`でログを標準出力に出力するようにします。"
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)


dumps = lambda content, *args, **kwargs: odumps(content, *args, **kwargs).decode()
"`orjson.dumps`を文字列で返すようにしたものです。"