"""

"""

from __future__ import annotations

import abc
import datetime
from dataclasses import dataclass
import re
import enum
import typing

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent

__all__ = [
    "Domain", "EncounterGame"
]


DOMAIN_REGEX = r"(?:http([s]?)\://)?([a-zA-Z0-9]+?)\.en\.cx"

CHROME_DEFAULT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'"
USER_AGENTS_FACTORY = UserAgent(fallback=CHROME_DEFAULT)


@dataclass
class Domain:
    name: str
    is_https: bool = False

    @property
    def full_url(self) -> str:
        letter = "s" if self.is_https else ""
        res = f"http{letter}://{self.name}.en.cx"
        return res

    @property
    def full_url_to_parse(self) -> str:
        res = f"{self.full_url}/?design=no"
        return res

    @classmethod
    def from_url(cls, url: str) -> Domain:
        url = url.lower()
        info = re.findall(DOMAIN_REGEX, url)[0]
        letter, name = info
        is_https = bool(letter)
        inst = cls(name, is_https)
        return inst

    def get_games(self) -> typing.List[EncounterGame]:
        ua = USER_AGENTS_FACTORY.random
        hdrs = {"User-Agent": ua}
        games_page = requests.get(self.full_url_to_parse, headers=hdrs).text
        soup = BeautifulSoup(games_page, 'lxml')
        tags = soup.find_all("div", class_="boxGameInfo")
        games = [
            EncounterGame.from_html(self, t)
            for t in tags
        ]
        return games


GAME_ID_RE = r"gid=([0-9]+)"
PARAMS = [
    "Game format:",
    "Passing sequence:",
    "Start of the game:",
    "The game completion time:",
]


# ABC
class CustomNamedEnum(enum.Enum):

    @classmethod
    @abc.abstractmethod
    def custom_names(cls) -> typing.Dict[CustomNamedEnum, str]:
        raise NotImplemented

    @property
    def name(self) -> str:
        res = self.custom_names()[self]
        return res

    @classmethod
    def from_str(cls, s: str) -> CustomNamedEnum:
        n_to_v = cls.__members__
        v_to_custom_n = cls.custom_names()
        n_to_v_full = {**n_to_v, **{v: k for k, v in v_to_custom_n.items()}}
        inst = n_to_v_full[s]
        return inst


class GameMode(CustomNamedEnum):
    Quest = enum.auto()
    Points = enum.auto()
    Brainstorm = enum.auto()
    Quiz = enum.auto()
    PhotoHunt = enum.auto()
    PhotoExtreme = enum.auto()
    GeoCaching = enum.auto()
    WetWars = enum.auto()
    Competition = enum.auto()

    @classmethod
    def custom_names(cls) -> typing.Dict[GameMode, str]:
        res = {
            cls.Quest: "Схватка",
            cls.Points: "Точки",
            cls.Brainstorm: "Мозговой штурм",
            cls.Quiz: "Викторина",
            cls.PhotoHunt: "Фотоохота",
            cls.PhotoExtreme: "Фотоэкстрим",
            cls.GeoCaching: "Кэшинг",
            cls.WetWars: "Мокрые войны",
            cls.Competition: "Конкурс",
        }
        return res


class GameFormat(CustomNamedEnum):
    Single = "Single"
    Team = "Team"

    @classmethod
    def custom_names(cls) -> typing.Dict[GameFormat, str]:
        return {
            cls.Single: "В одиночку",
            cls.Team: "Командами",
        }


class PassingSequence(CustomNamedEnum):
    Linear = "Linear"
    Storm = "Storm"
    Custom = "Custom (not inear)"
    Random = "Random"
    DynamicallyRandom = "Dinamically random"

    @classmethod
    def custom_names(cls) -> typing.Dict[PassingSequence, str]:
        return {
            cls.Linear: "Линейная",
            cls.Storm: "Штурмовая",
            cls.Custom: "Указанная (не линейная)",
            cls.Random: "Случайная",
            cls.DynamicallyRandom: "Динамически случайная",
        }


@dataclass
class EncounterGame:
    domain: Domain
    game_id: int
    game_name: str
    _game_mode: typing.Union[str, GameMode]
    _game_format: typing.Union[str, GameFormat]
    _passing_sequence: typing.Union[str, PassingSequence]
    _start_time: typing.Union[str, datetime.datetime]
    _end_time: typing.Union[str, datetime.datetime]
    player_ids: typing.List[int]

    @property
    def game_format(self) -> GameFormat:
        if not isinstance(self._game_format, GameFormat):
            return GameFormat.from_str(self._game_format)
        else:
            return self._game_format

    @property
    def passing_sequence(self) -> PassingSequence:
        if not isinstance(self._passing_sequence, PassingSequence):
            return PassingSequence.from_str(self._passing_sequence)
        else:
            return self._passing_sequence

    @property
    def game_mode(self) -> GameMode:
        if not isinstance(self._game_mode, GameMode):
            return GameMode.from_str(self._game_mode)
        else:
            return self._game_mode

    @staticmethod
    def _parse_time(time: str) -> datetime.datetime:
        # noinspection PyBroadException
        try:
            dt = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        except Exception:
            # noinspection PyBroadException
            try:
                d, t = time.split(" ")[:2]
                d = d[:10]
                t = t[:8]
                new_time = f"{d} {t}"
                dt = datetime.datetime.strptime(new_time, "%d.%m.%Y %H:%M:%S")
            except Exception:
                d, t, *rest = time.split(" ")

                if rest:
                    loc, *_ = rest
                    loc = loc[:2]
                    args = [d, t, loc]
                else:
                    args = [d, t]
                pts = " ".join(args)
                fmt = "%m/%d/%Y %I:%M:%S"
                if len(args) > 2:
                    fmt += " %p"
                dt = datetime.datetime.strptime(pts, fmt)
        return dt

    @property
    def start_time(self) -> datetime.datetime:
        if not isinstance(self._start_time, datetime.datetime):
            dt = self._parse_time(self._start_time)
        else:
            dt = self._start_time
        return dt

    @property
    def end_time(self) -> datetime.datetime:
        if not isinstance(self._end_time, datetime.datetime):
            dt = self._parse_time(self._end_time)
        else:
            dt = self._end_time
        return dt

    @staticmethod
    def find_player_id(href: str) -> int:
        try:
            m = re.findall(r"\?tid=([0-9]+)", href)[0]
        except IndexError:
            m = re.findall(r"\?uid=([0-9]+)", href)[0]
        player_id = int(m)
        return player_id

    @staticmethod
    def get_id_(elem: Tag) -> typing.Optional[str]:
        # noinspection PyBroadException
        try:
            id_ = elem.parent.find_all("span")[1].find("span")["id"]
        except Exception:
            id_ = None
        return id_

    @classmethod
    def from_html(cls, domain: Domain, html: Tag) -> EncounterGame:
        meta = html.find("a", {"id": "lnkGameTitle"})
        name = meta.text
        url = meta["href"]
        id_ = int(re.findall(GAME_ID_RE, url)[0])

        game_mode = html.find("img", id="ImgGameType")["title"]
        spans = html.find_all("span", class_="title")
        format_, seq_ = [s.parent.find_all("span")[1].text for s in spans[:2]]

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

        inst = cls(domain, id_, name, game_mode, format_, seq_, start, end, player_ids)
        return inst

    @property
    def game_details_url(self) -> str:
        res = f'GameDetails.aspx?gid={self.game_id}'
        return res

    @property
    def game_details_full_url(self) -> str:
        res = f"{self.domain.full_url}/{self.game_details_url}"
        return res

    @classmethod
    def from_json(
            cls,
            json: typing.Union[
                typing.Dict[str, typing.Any],
                pd.Series
            ]
    ) -> EncounterGame:
        ids_ = cls.player_ids_from_string(json["PLAYER_IDS"])
        domain = Domain.from_url(json["DOMAIN"])

        inst = cls(
            domain,
            json["ID"], json["NAME"], json["MODE"],
            json["FORMAT"], json["PASSING_SEQUENCE"],
            json["START_TIME"], json["END_TIME"],
            ids_,
        )
        return inst

    @property
    def player_ids_str(self) -> str:
        res = ",".join(map(str, self.player_ids))
        return res

    @staticmethod
    def player_ids_from_string(player_ids: str) -> typing.List[int]:
        if player_ids:
            player_ids_int = [
                int(el)
                for el in player_ids.split(",")
            ]
        else:
            player_ids_int = []
        return player_ids_int

    def to_json(self) -> typing.Dict[str, typing.Any]:
        di = {
            "DOMAIN": self.domain.full_url,
            "ID": self.game_id,
            "NAME": self.game_name,
            "MODE": self.game_mode.name,
            "FORMAT": self.game_format.name,
            "PASSING_SEQUENCE": self.passing_sequence.name,
            "START_TIME": self.start_time,
            "END_TIME": self.end_time,
            "PLAYER_IDS": self.player_ids_str,
        }
        return di

    def __str__(self) -> str:
        pts = [
            f"<b>{self.game_name}</b> (id <a href='{self.game_details_full_url}' target='_blank'>{self.game_id}</a>)",
            f"{self.game_mode.name}, {self.passing_sequence.name} ({self.game_format.name})",
            f"{self.start_time} -> {self.end_time}",
            f"Players registered: {len(self.player_ids)}",
        ]
        res = "\n".join(pts)
        return res


if __name__ == '__main__':
    # games_ = Domain.from_url("http://kramatorsk.en.cx").get_games()
    games_ = Domain.from_url("http://kharkiv.en.cx").get_games()
    print(list(map(str, games_)))
    # print(PassingSequence.from_str("Linear"))
    # print(PassingSequence.from_str("Линейная"))
    # print(GameFormat.from_str("Командная"))
    # print(GameFormat.from_str("Team"))
    # print(GameFormat.from_str("Storsm"))
