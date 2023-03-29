"Rext Lib - Quick Two Log"

__all__ = ("QuickTwoLog", "InfoCache")

from dataclasses import dataclass

from logging import Logger


@dataclass
class QuickTwoLog:
    "簡単に処理前後のログを出すためのもの。"

    logger: Logger
    before: str | None = None
    after: str | None = None

    def __post_init__(self) -> None:
        if self.before is None:
            raise ValueError("`.before`が設定されていません。")
        if self.after is None:
            raise ValueError("`.after`が設定されていません。")

    def __enter__(self) -> None:
        self.logger.info(self.before)

    def __exit__(self, *_) -> None:
        self.logger.info(self.after)


class InfoCache(QuickTwoLog):
    "キャッシュの読み込み中と表示するためのクラスです。"

    def __post_init__(self) -> None:
        self.before = self.before or "キャッシュを読み込み中..."
        self.after = self.after or "キャッシュを読み込みました。"