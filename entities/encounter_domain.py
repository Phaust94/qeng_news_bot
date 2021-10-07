"""
Encounter-specific domain
"""

from __future__ import annotations

import re
import typing
from urllib.parse import urlsplit, parse_qs


import requests
# noinspection PyProtectedMember
from bs4 import BeautifulSoup, Tag


from entities.constants import USER_AGENTS_FACTORY
from entities.game import BaseGame
from entities.domain import Domain
from entities.game_attrs import GameMode
from entities.feed import Forum

__all__ = [
    "EncounterDomain",
    "EncounterGame",
]

GAME_ID_RE = r"gid=([0-9]+)"


class EncounterDomain(Domain):

    @property
    def full_url_template(self) -> str:
        res = f"{self.base_url}/{{path}}?lang={self.language.to_str()}{{args}}"
        return res

    @property
    def full_url(self) -> str:
        res = f"{self.base_url}?lang={self.language.to_str()}"
        return res

    @property
    def full_url_to_parse(self):
        res = f"{self.full_url}&design=no"
        return res

    @property
    def forum_url(self) -> typing.Optional[str]:
        res = self.full_url_template.format(path="export/Syndication/ForumRss.aspx", args="")
        return res

    def get_games(self) -> typing.List[BaseGame]:
        ua = USER_AGENTS_FACTORY.random
        hdrs = {"User-Agent": ua}
        games_page = requests.get(self.full_url_to_parse, headers=hdrs).text
        soup = BeautifulSoup(games_page, 'lxml')
        tags = soup.find_all("div", class_="boxGameInfo")
        forum = Forum.from_url(self.forum_url)
        games = [
            EncounterGame.from_html(self, t, forum)
            for t in tags
        ]
        return games


class EncounterGame(BaseGame):

    @staticmethod
    def get_id_(elem: Tag) -> typing.Optional[str]:
        # noinspection PyBroadException
        try:
            id_ = elem.parent.find_all("span")[1].find("span")["id"]
        except Exception:
            id_ = None
        return id_

    @staticmethod
    def find_player_id(href: str) -> int:
        try:
            m = re.findall(r"\?tid=([0-9]+)", href)[0]
        except IndexError:
            m = re.findall(r"\?uid=([0-9]+)", href)[0]
        player_id = int(m)
        return player_id

    @classmethod
    def from_html(cls, domain: Domain, html: Tag, forum: Forum) -> EncounterGame:
        meta = html.find("a", {"id": "lnkGameTitle"})
        name = meta.text
        url = meta["href"]
        id_ = int(re.findall(GAME_ID_RE, url)[0])

        game_mode = html.find("img", id="ImgGameType")["title"]
        game_mode = GameMode.from_str(game_mode)
        spans = html.find_all("span", class_="title")
        is_judged = game_mode in {GameMode.Competition, GameMode.PhotoHunt}
        if not is_judged:
            format_, seq_ = [s.parent.find_all("span")[1].text for s in spans[:2]]
        else:
            format_ = spans[0].parent.find_all("span")[1].text
            seq_ = "Linear"
        local_time_id = html.select('[id*="gameInfo_enContPanel_lblYourTime"]')[0]["id"]
        all_ids = [cls.get_id_(el) for el in spans]
        ind = all_ids.index(local_time_id)
        start, end = [
            el.parent.find_all("span")[1].next
            for el in [
                spans[ind - 1],
                spans[ind + 1]
            ]
        ]

        players = html.find_all("a", id="lnkPlayerInfo")
        player_hrefs = [p["href"] for p in players]
        player_ids = [cls.find_player_id(p) for p in player_hrefs]
        player_ids = sorted(player_ids)

        game_descr = html.find("div", class_="divDescr").text
        game_descr = cls.strip_description_text(game_descr)

        authors = [
            el.text
            for el in spans[ind - 2 - is_judged].parent.find_all("a", id="lnkAuthor")
        ]
        author_ids = [
            int(el["href"].split("=")[-1])
            for el in spans[ind - 2 - is_judged].parent.find_all("a", id="lnkAuthor")
        ]

        thread_elem = html.find("a", id="lnkGbTopic")
        if thread_elem is not None:
            thread_url = thread_elem["href"]
            sp = urlsplit(thread_url)
            params = parse_qs(sp.query)
            # noinspection PyTypeChecker
            tid = int(params["topic"][0])
        else:
            tid = None
        entry = forum[tid]
        if entry is not None:
            msg_id, msg = entry.msg_id, str(entry)
        else:
            msg_id, msg = None, None

        inst = cls(
            domain, id_, name,
            game_mode, format_, seq_,
            start, end,
            player_ids,
            game_descr,
            authors, author_ids, tid,
            msg_id, msg,
        )
        return inst

    @classmethod
    def _forum_url(cls, domain: Domain, forum_thread_id: int) -> str:
        res = domain.full_url_template.format(
            path="Guestbook/Messages.aspx",
            args=f"&topic={forum_thread_id}"
        )
        return res

    @classmethod
    def _game_details_full_url(cls, domain: Domain, game_id: int) -> str:
        res = domain.full_url_template.format(
            path="GameDetails.aspx",
            args=f"&gid={game_id}"
        )
        return res


if __name__ == '__main__':
    for dom_ in [
        "kharkiv.en.cx",
        # "game.qeng.org",
    ]:
        dom_inst_ = Domain.from_url(dom_)
        print(dom_inst_, dom_inst_.full_url_to_parse)
        games_ = dom_inst_.get_games()
        print(games_)
