"""

"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
import re
import enum
import typing
import hashlib

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent

from constants import MAX_DESCRIPTION_LENGTH

__all__ = [
    "Domain", "EncounterGame", "Rule",
    "GameMode", "GameFormat", "PassingSequence",
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

    def __str__(self) -> str:
        return self.full_url


GAME_ID_RE = r"gid=([0-9]+)"
PARAMS = [
    "Game format:",
    "Passing sequence:",
    "Start of the game:",
    "The game completion time:",
]


class Language(enum.Enum):
    Russian = enum.auto()
    English = enum.auto()


# ABC
class CustomNamedEnum(enum.Enum):

    def localized_name(self, language: Language) -> str:
        res = self.localization_dict()[self][language]
        return res

    @classmethod
    def from_str(cls, s: str) -> CustomNamedEnum:
        localized_name_to_inst = {
            loc_name: type_
            for type_, loc_ in cls.localization_dict().items()
            for lang, loc_name in loc_.items()
        }
        inst = localized_name_to_inst[s]
        return inst

    @classmethod
    def localization_dict(cls) -> typing.Dict[CustomNamedEnum, typing.Dict[Language, str]]:
        raise NotImplementedError


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
    def localization_dict(cls) -> typing.Dict[GameMode, typing.Dict[Language, str]]:
        di = {
            cls.Quest: {
                Language.Russian: "Схватка",
                Language.English: "Quest",
            },
            cls.Points: {
                Language.Russian: "Точки",
                Language.English: "Points",
            },
            cls.Brainstorm: {
                Language.Russian: "Мозговой штурм",
                Language.English: "Brainstorm",
            },
            cls.Quiz: {
                Language.Russian: "Викторина",
                Language.English: "Quiz",
            },
            cls.PhotoHunt: {
                Language.Russian: "Фотоохота",
                Language.English: "PhotoHunt",
            },
            cls.PhotoExtreme: {
                Language.Russian: "Фотоэкстрим",
                Language.English: "PhotoExtreme",
            },
            cls.GeoCaching: {
                Language.Russian: "Кэшинг",
                Language.English: "GeoCaching",
            },
            cls.WetWars: {
                Language.Russian: "Мокрые войны",
                Language.English: "WetWars",
            },
            cls.Competition: {
                Language.Russian: "Конкурс",
                Language.English: "Competition",
            },
        }
        return di


class GameFormat(CustomNamedEnum):
    Single = enum.auto()
    Team = enum.auto()

    @classmethod
    def localization_dict(cls) -> typing.Dict[GameFormat, typing.Dict[Language, str]]:
        di = {
            cls.Single: {
                Language.Russian: "В одиночку",
                Language.English: "Single",
            },
            cls.Team: {
                Language.Russian: "Командами",
                Language.English: "Team",
            },
        }
        return di

    def members_text(self, lang: Language) -> str:
        cls = self.__class__
        di = {
            cls.Single: {
                Language.Russian: "Игроков зарегистрировано",
                Language.English: "Players registered",
            },
            cls.Team: {
                Language.Russian: "Команд зарегистрировано",
                Language.English: "Teams registered",
            },
        }
        return di[self][lang]


class PassingSequence(CustomNamedEnum):
    Linear = enum.auto()
    Storm = enum.auto()
    Custom = enum.auto()
    Random = enum.auto()
    DynamicallyRandom = enum.auto()

    @classmethod
    def localization_dict(cls) -> typing.Dict[CustomNamedEnum, typing.Dict[Language, str]]:
        di = {
            cls.Linear: {
                Language.Russian: "Линейная",
                Language.English: "Linear",
            },
            cls.Storm: {
                Language.Russian: "Штурмовая",
                Language.English: "Storm",
            },
            cls.Custom: {
                Language.Russian: "Указанная (не линейная)",
                Language.English: "Custom (not inear)",
            },
            cls.Random: {
                Language.Russian: "Случайная",
                Language.English: "Random",
            },
            cls.DynamicallyRandom: {
                Language.Russian: "Динамически случайная",
                Language.English: "Dinamically random",
            },
        }
        return di


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
    game_description: str

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

        game_descr = html.find("div", class_="divDescr").text
        nbsp = u'\xa0'
        game_descr = game_descr.replace(nbsp, "").replace("\n\n", "\n").replace("\n \n", "\n")

        inst = cls(domain, id_, name, game_mode, format_, seq_, start, end, player_ids, game_descr)
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

        desc = json["DESCRIPTION_TRUNCATED"]
        if json["DESCRIPTION_REAL_LENGTH"] > MAX_DESCRIPTION_LENGTH and desc.endswith("..."):
            desc = desc[:-3]

        inst = cls(
            domain,
            json["ID"], json["NAME"], GameMode(json["MODE"]),
            GameFormat(json["FORMAT"]), PassingSequence(json["PASSING_SEQUENCE"]),
            json["START_TIME"], json["END_TIME"],
            ids_, desc,
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

    @property
    def game_description_truncated(self) -> str:
        res = self.game_description[:MAX_DESCRIPTION_LENGTH]
        if len(self.game_description) > MAX_DESCRIPTION_LENGTH:
            res += "..."
        return res

    def to_json(self) -> typing.Dict[str, typing.Any]:
        di = {
            "DOMAIN": self.domain.full_url,
            "ID": self.game_id,
            "NAME": self.game_name,
            "MODE": self.game_mode.value,
            "FORMAT": self.game_format.value,
            "PASSING_SEQUENCE": self.passing_sequence.value,
            "START_TIME": self.start_time,
            "END_TIME": self.end_time,
            "PLAYER_IDS": self.player_ids_str,
            "DESCRIPTION_TRUNCATED": self.game_description_truncated,
            "DESCRIPTION_REAL_LENGTH": len(self.game_description),
        }
        return di

    def to_str(self, lang: Language) -> str:
        mem_txt = self.game_format.members_text(lang)
        desc = {
            lang.Russian: "Описание",
            lang.English: "Description",
        }[lang]
        game_props = [
            self.game_mode.localized_name(lang),
            self.passing_sequence.localized_name(lang),
            self.game_format.localized_name(lang),
        ]
        pts = [
            f"<b>{self.game_name}</b> (id <a href='{self.game_details_full_url}' target='_blank'>{self.game_id}</a>)",
            "{}, {} ({})".format(*game_props),
            f"{self.start_time} -> {self.end_time}",
            f"{mem_txt}: {len(self.player_ids)}",
            f"{desc}: {self.game_description_truncated}"
        ]
        res = "\n".join(pts)
        return res

    def __str__(self) -> str:
        res = self.to_str(Language.Russian)
        return res


@dataclass
class Rule:
    domain: typing.Optional[Domain] = None
    player_id: typing.Optional[int] = None
    team_id: typing.Optional[int] = None
    game_id: typing.Optional[int] = None

    @property
    def rule_id(self) -> str:
        to_hash = [
            self.domain or "",
            self.player_id or "",
            self.team_id or "",
            self.game_id or "",
        ]
        to_hash = "".join(str(x) for x in to_hash)
        rule_id = hashlib.md5(to_hash.encode()).hexdigest()[:10]
        return rule_id

    def to_json(self) -> typing.Dict[str, typing.Any]:
        j = {
            "RULE_ID": self.rule_id,
            "DOMAIN": str(self.domain) if self.domain else None,
            "PLAYER_ID": self.player_id,
            "TEAM_ID": self.team_id,
            "GAME_ID": self.game_id,
        }
        return j

    @classmethod
    def from_json(cls, j: typing.Dict[str, typing.Any]):
        dom = j["DOMAIN"]
        if dom:
            dom = Domain.from_url(dom)
        inst = cls(
            dom,
            j["PLAYER_ID"],
            j["TEAM_ID"],
            j["GAME_ID"],
        )
        return inst


if __name__ == '__main__':
    # games_ = Domain.from_url("http://kramatorsk.en.cx").get_games()
    games_ = Domain.from_url("http://kharkiv.en.cx").get_games()
    print(list(map(str, games_)))
    print("a")
    # print(GameMode(1))
    # print(PassingSequence.from_str("Linear"))
    # print(PassingSequence.from_str("Линейная"))
    # print(GameFormat.from_str("Командами"))
    # print(GameFormat.from_str("Team"))
    # print(GameFormat.from_str("Storm"))
