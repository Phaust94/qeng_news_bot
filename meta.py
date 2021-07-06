"""

"""

from __future__ import annotations

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

    @classmethod
    def from_url(cls, url: str) -> Domain:
        info = re.findall(DOMAIN_REGEX, url)[0]
        letter, name = info
        is_https = bool(letter)
        inst = cls(name, is_https)
        return inst

    def get_games(self) -> typing.List[EncounterGame]:
        ua = USER_AGENTS_FACTORY.random
        hdrs = {"User-Agent": ua}
        games_page = requests.get(self.full_url, headers=hdrs).text
        soup = BeautifulSoup(games_page, 'lxml')
        tags = soup.find_all("div", class_="boxGameInfo")
        games = [
            EncounterGame.from_html(t)
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


class GameFormat(CustomNamedEnum):
    Single = "Single"
    Team = "Team"

    @classmethod
    def custom_names(cls) -> typing.Dict[GameFormat, str]:
        return {
            cls.Single: "Одиночная",
            cls.Team: "Командная",
        }


class PassingSequence(CustomNamedEnum):
    Linear = "Linear"
    Storm = "Storm"

    @classmethod
    def custom_names(cls) -> typing.Dict[PassingSequence, str]:
        return {
            cls.Linear: "Линейная",
            cls.Storm: "Штурмовая",
        }


@dataclass
class EncounterGame:
    game_id: int
    game_name: str
    _game_format: typing.Union[str, GameFormat]
    _passing_sequence: typing.Union[str, PassingSequence]
    _start_time: typing.Union[str, datetime.datetime]
    _end_time: typing.Union[str, datetime.datetime]

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

    @staticmethod
    def _parse_time(time: str) -> datetime.datetime:
        # noinspection PyBroadException
        try:
            dt = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        except Exception:
            d, t, loc, *_ = time.split(" ")
            loc = loc[:2]
            pts = " ".join([d, t, loc])
            dt = datetime.datetime.strptime(pts, "%m/%d/%Y %I:%M:%S %p")
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

    @classmethod
    def from_html(cls, html: Tag) -> EncounterGame:
        meta = html.find("a", {"id": "lnkGameTitle"})
        name = meta.text
        url = meta["href"]
        id_ = int(re.findall(GAME_ID_RE, url)[0])
        vals = []
        for param in PARAMS:
            t = html.find("span", class_="title", text=param)
            val = t.parent.find_all("span")[1].text
            vals.append(val)

        inst = cls(id_, name, *vals)
        return inst

    @property
    def game_details_url(self) -> str:
        res = f'/GameDetails.aspx?gid={self.game_id}'
        return res

    @classmethod
    def from_json(
            cls,
            json: typing.Union[
                typing.Dict[str, typing.Any],
                pd.Series
            ]
    ) -> EncounterGame:
        inst = cls(
            json["ID"], json["NAME"],
            json["FORMAT"], json["PASSING_SEQUENCE"],
            json["START_TIME"], json["END_TIME"],
        )
        return inst

    def to_json(self) -> typing.Dict[str, typing.Any]:
        di = {
            "ID": self.game_id,
            "NAME": self.game_name,
            "FORMAT": self.game_format.name,
            "PASSING_SEQUENCE": self.passing_sequence.name,
            "START_TIME": self.start_time,
            "END_TIME": self.end_time,
        }
        return di

    def __str__(self) -> str:
        pts = [
            f"{self.game_name} (id {self.game_id})",
            f"{self.game_format.name} {self.passing_sequence.name}",
            f"{self.start_time} -> {self.end_time}",
        ]
        res = "\n".join(pts)
        return res


if __name__ == '__main__':
    Domain.from_url("http://kharkiv.en.cx").get_games()
    # print(PassingSequence.from_str("Linear"))
    # print(PassingSequence.from_str("Линейная"))
    # print(GameFormat.from_str("Командная"))
    # print(GameFormat.from_str("Team"))
    # print(GameFormat.from_str("Storsm"))
