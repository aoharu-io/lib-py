# rtlib - Main

import logging

from . import utils


__all__ = ("utils", "set_handler")


def set_handler(logger: logging.Logger) -> None:
    "渡された`Logger`でログを標準出力に出力するようにします。"
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)