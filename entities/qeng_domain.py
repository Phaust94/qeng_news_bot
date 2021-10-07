"""
QEng-specific domain
"""

from __future__ import annotations

import typing

import feedparser
from bs4 import BeautifulSoup

from entities.domain import Domain
from entities.game import BaseGame
from entities.constants import USER_AGENTS_FACTORY
from entities.game_attrs import GameMode, GameFormat, PassingSequence

__all__ = [
    "QEngDomain",
    "QEngGame",
]


class QEngDomain(Domain):

    @property
    def full_url(self) -> str:
        return self.base_url

    @property
    def full_url_template(self) -> str:
        res = f"{self.base_url}/{{path}}?{{args}}"
        return res

    @property
    def full_url_to_parse(self):
        res = f"{self.full_url}/rss.php"
        return res

    @property
    def forum_url(self) -> typing.Optional[str]:
        return None

    def get_games(self) -> typing.List[BaseGame]:
        games_feed = feedparser.parse(self.full_url_to_parse, agent=USER_AGENTS_FACTORY.random)
        games = [
            QEngGame.from_feed(self, fe)
            for fe in games_feed.entries
            if not fe.title.startswith("#")
        ]
        return games


class QEngGame(BaseGame):

    @classmethod
    def from_feed(cls, domain: Domain, fe: feedparser.FeedParserDict) -> QEngGame:
        descr = fe.summary
        descr_soup = BeautifulSoup(descr, 'lxml')
        descr_text = descr_soup.text
        descr_text = cls.strip_description_text(descr_text)
        if not fe.authors:
            authors_names = []
        else:
            authors_names = fe.authors.split(", ")

        g = cls(
            domain, int(fe.gid),
            fe.title,
            GameMode.Brainstorm if int(fe.kind) == 4 else GameMode.Quest,
            GameFormat.Single if int(fe.single) else GameFormat.Team,
            PassingSequence.Linear,
            fe.start_date,
            fe.end_date,
            [],      # TODO: fix this when Recar updates
            descr_text,
            authors_names, [],
            None, None, None,
        )

        return g

    @classmethod
    def _forum_url(cls, domain: Domain, forum_thread_id: int) -> None:
        return None

    @classmethod
    def _game_details_full_url(cls, domain: QEngDomain, game_id: int) -> str:
        res = domain.full_url_template.format(
            path="index.php",
            args=f"gid={game_id}"
        )
        return res


if __name__ == '__main__':
    for dom_ in [
        "game.qeng.org",
    ]:
        dom_inst_ = Domain.from_url(dom_)
        print(dom_inst_, dom_inst_.full_url_to_parse)
        games_ = dom_inst_.get_games()
        print(games_)
