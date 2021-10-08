"""
QEng-specific domain
"""

from __future__ import annotations

import datetime
import typing

import requests
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
        res = f"{self.full_url}/api_games_list.php"
        return res

    @property
    def forum_url(self) -> typing.Optional[str]:
        return None

    def get_games(self) -> typing.List[BaseGame]:
        ua = USER_AGENTS_FACTORY.random
        hdrs = {"User-Agent": ua}
        games_page = requests.get(self.full_url_to_parse, headers=hdrs).json()
        games = [
            QEngGame.from_api(self, fe)
            for fe in games_page
        ]
        return games

    @property
    def game_details_url(self) -> typing.Tuple[str, str]:
        return "index.php", "gid={id}"

    @property
    def team_details_url(self) -> typing.Tuple[str, str]:
        return "team.php", "team_id={id}"

    @property
    def user_details_url(self) -> typing.Tuple[str, str]:
        return "view_user.php", "user_id={id}"


class QEngGame(BaseGame):

    @classmethod
    def from_feed(cls, domain: Domain, fe: feedparser.FeedParserDict) -> QEngGame:
        descr = fe.summary
        descr_soup = BeautifulSoup(descr or '', 'lxml')
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
    def from_api(cls, domain: Domain, g: typing.Dict[str, typing.Any]) -> QEngGame:
        descr = g["description"]
        descr_soup = BeautifulSoup(descr or '', 'lxml').text
        descr_soup = BeautifulSoup(descr_soup or '', 'lxml').text
        descr_text = cls.strip_description_text(descr_soup)
        authors_ids = [int(a["uid"]) for a in g["authors"]]
        authors_names = [a["username"] for a in g["authors"]]
        teams = [
            int(t["id"])
            for t in g["teams"]
            if int(t["status"]) in {0, 1}
        ]
        name = BeautifulSoup(g["name"] or '', "lxml").text

        g = cls(
            domain, int(g["id"]),
            name,
            GameMode.Brainstorm if int(g["kind"]) == 4 else GameMode.Quest,
            GameFormat.Single if int(g["single"]) else GameFormat.Team,
            PassingSequence.Linear if int(g["type"]) == 1 else PassingSequence.Storm,
            datetime.datetime.utcfromtimestamp(int(g["start_time_f"])),
            datetime.datetime.utcfromtimestamp(int(g["end_time_f"])),
            teams,
            descr_text,
            authors_names, authors_ids,
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
