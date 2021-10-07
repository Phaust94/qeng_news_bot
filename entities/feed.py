"""
Forum feed
"""

from __future__ import annotations

from dataclasses import dataclass
import typing
from urllib.parse import urlsplit, parse_qs

# noinspection PyProtectedMember
from bs4 import BeautifulSoup
import feedparser

from entities.constants import USER_AGENTS_FACTORY

__all__ = [
    "FeedEntry", "Forum",
]


@dataclass
class FeedEntry:
    topic_id: int
    msg_id: int
    author: str
    msg: str

    @classmethod
    def from_json(cls, j: typing.Dict[str, typing.Any]) -> FeedEntry:
        url = j["link"]
        sp = urlsplit(url)
        params = parse_qs(sp.query)
        msg_id = int(sp[-1])
        # noinspection PyTypeChecker
        tid = int(params["topic"][0])
        summ = BeautifulSoup(j["summary"], 'lxml').text
        inst = cls(
            tid, msg_id,
            j["author"],
            summ,
        )
        return inst

    def __str__(self) -> str:
        res = f"{self.author}: {self.msg}"
        return res


@dataclass
class Forum:
    feed_entries: typing.List[FeedEntry]

    @property
    def msg_dict(self) -> typing.Dict[int, FeedEntry]:
        di = [
            (en.topic_id, en)
            for en in self.feed_entries
        ]
        res = dict(reversed(di))

        return res

    @classmethod
    def from_url(cls, forum_url: typing.Optional[str]) -> Forum:
        if forum_url is not None:
            feed = feedparser.parse(forum_url, agent=USER_AGENTS_FACTORY.random)
            entries = [FeedEntry.from_json(e) for e in feed.entries]
        else:
            entries = []
        inst = cls(entries)
        return inst

    def __getitem__(self, item) -> FeedEntry:
        return self.msg_dict.get(item)
