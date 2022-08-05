# rtlib - Log

from logging.handlers import RotatingFileHandler
import logging

from os import mkdir
from os.path import exists


BASE_FORMAT = "[%(name)s] [%(levelname)s] %(message)s"
NORMAL_FORMATTER = logging.Formatter(BASE_FORMAT)
EXTENDED_FORMATTER = logging.Formatter(f"[%(asctime)s] {BASE_FORMAT}", "%Y-%m-%d %H:%M:%S")


def set_handler(logger: logging.Logger, output_file: bool = True) -> None:
    "渡された`Logger`でログを標準出力に出力するようにします。オプションでファイル出力します。"
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(NORMAL_FORMATTER)
    logger.addHandler(handler)
    if output_file:
        if not exists("data/logs"):
            mkdir("data/logs")
        more = ""
        if exists("core/bot.py"):
            # もしBotによるログ出力ならシャードIDを出力先ファイルの名前に入れる。
            from core.tdpocket import bot
            assert bot is not None
            more = bot.rtws.id_
        handler = RotatingFileHandler(
            filename="data/logs/rt%s.log" % more, encoding='utf-8', mode='w',
            maxBytes=32 * 1024 * 1024, backupCount=10
        )
        handler.setFormatter(EXTENDED_FORMATTER)
        logger.addHandler(handler)