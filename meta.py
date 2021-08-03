"""

"""

from __future__ import annotations

import datetime
import itertools
from dataclasses import dataclass, fields, Field
import re
import enum
import typing
import hashlib
from urllib.parse import urlsplit, parse_qs
import os
import time
from io import BytesIO
import tempfile
from contextlib import contextmanager

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
import feedparser
from selenium import webdriver
from PIL import Image

from constants import MAX_DESCRIPTION_LENGTH, MAX_DESCRIPTION_LENGTH_TG, MAX_LAST_MESSAGE_LENGTH,\
    SALT, RULE_ID_LENGTH
from translations import Language, MenuItem, MENU_LOCALIZATION
from description_diff import html_diffs

__all__ = [
    "Domain", "EncounterGame", "Rule",
    "GameMode", "GameFormat", "PassingSequence",
    "Language", "MenuItem", "Update",
]


DOMAIN_REGEX = r"([a-zA-Z0-9]+?)\.en\.cx"
# LANGUAGE_REGEX = r"\?.*?lang=([a-zA-Z])"

CHROME_DEFAULT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'"
USER_AGENTS_FACTORY = UserAgent(fallback=CHROME_DEFAULT)


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
    def from_url(cls, forum_url: str):
        feed = feedparser.parse(forum_url, agent=USER_AGENTS_FACTORY.random)
        entries = [FeedEntry.from_json(e) for e in feed.entries]
        inst = cls(entries)
        return inst

    def __getitem__(self, item) -> FeedEntry:
        return self.msg_dict.get(item)


@dataclass
class Domain:
    name: str
    language: Language = Language.Russian
    is_https: bool = False

    @property
    def base_url(self) -> str:
        letter = "s" if self.is_https else ""
        res = f"http{letter}://{self.name}.en.cx"
        return res

    @property
    def full_url(self) -> str:
        res = f"{self.base_url}?lang={self.language.to_str()}"
        return res

    @property
    def full_url_template(self) -> str:
        res = f"{self.base_url}/{{path}}?lang={self.language.to_str()}{{args}}"
        return res

    @property
    def full_url_to_parse(self) -> str:
        res = f"{self.full_url}&design=no"
        return res

    @property
    def forum_url(self) -> str:
        res = self.full_url_template.format(path="export/Syndication/ForumRss.aspx", args="")
        return res

    @classmethod
    def from_url(cls, url: str) -> Domain:
        url = url.lower()
        if not url.startswith("http"):
            url = f"http://{url}"
        sp = urlsplit(url)
        is_https = sp.scheme == 'https'
        params = parse_qs(sp.query)
        lang = params.get("lang", [''])[0]
        dom = re.findall(DOMAIN_REGEX, sp.netloc)[0]
        if dom.startswith("m."):
            dom = dom[2:]
        lang = Language.from_str(lang)
        inst = cls(dom, lang, is_https)
        return inst

    def get_games(self) -> typing.List[EncounterGame]:
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

    def __str__(self) -> str:
        return self.full_url


GAME_ID_RE = r"gid=([0-9]+)"


# ABC
class CustomNamedEnum(enum.Enum):

    @classmethod
    def _default_value(cls) -> CustomNamedEnum:
        raise NotImplementedError

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
        inst = localized_name_to_inst.get(s, cls._default_value())
        return inst

    @classmethod
    def localization_dict(cls) -> typing.Dict[CustomNamedEnum, typing.Dict[Language, str]]:
        di = {
            v: MENU_LOCALIZATION[getattr(MenuItem, f"{cls.__name__}{k}")]
            for k, v in cls.__members__.items()
        }
        return di


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
    def _default_value(cls) -> GameMode:
        return cls.Points

    # @classmethod
    # def localization_dict(cls) -> typing.Dict[GameMode, typing.Dict[Language, str]]:
    #     di = {
    #         v: getattr(MenuItem, f"GameType{k}")
    #         for k, v in cls.__members__.items()
    #     }
    #     return di


class GameFormat(CustomNamedEnum):
    Single = enum.auto()
    Team = enum.auto()
    Personal = enum.auto()

    @classmethod
    def _default_value(cls) -> GameFormat:
        return cls.Single

    # @classmethod
    # def localization_dict(cls) -> typing.Dict[GameFormat, typing.Dict[Language, str]]:
    #     di = {
    #         v: MENU_LOCALIZATION[getattr(MenuItem, f"GameFormat{k}")]
    #         for k, v in cls.__members__.items()
    #     }
    #     return di

    def members_text(self, lang: Language) -> str:
        cls = self.__class__
        di = {
            v: MENU_LOCALIZATION[getattr(MenuItem, f"GameFormatMembers{k}")]
            for k, v in cls.__members__.items()
        }
        return di[self][lang]


class PassingSequence(CustomNamedEnum):
    Linear = enum.auto()
    Storm = enum.auto()
    Custom = enum.auto()
    Random = enum.auto()
    DynamicallyRandom = enum.auto()

    @classmethod
    def _default_value(cls) -> PassingSequence:
        return cls.Linear

    # @classmethod
    # def localization_dict(cls) -> typing.Dict[PassingSequence, typing.Dict[Language, str]]:
    #     di = {
    #         v: getattr(MenuItem, f"PassingSequence{k}")
    #         for k, v in cls.__members__.items()
    #     }
    #     return di


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
    authors: typing.List[str]
    author_ids: typing.List[int]
    forum_thread_id: int
    last_comment_id: typing.Optional[int]
    last_comment_text: typing.Optional[str]

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
    def _parse_time(time_: str) -> datetime.datetime:
        # noinspection PyBroadException
        try:
            dt = datetime.datetime.strptime(time_, "%Y-%m-%d %H:%M:%S")
        except Exception:
            # noinspection PyBroadException
            try:
                d, t = time_.split(" ")[:2]
                d = d[:10]
                if t.endswith("("):
                    t = t[:-2]
                new_time = f"{d} {t}"
                dt = datetime.datetime.strptime(new_time, "%d.%m.%Y %H:%M:%S")
            except Exception:
                d, t, *rest = time_.split(" ")

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

    @property
    def authors_list_str(self) -> str:
        return "%".join(self.authors)

    @property
    def authors_ids_list_str(self) -> str:
        return "%".join(map(str, self.author_ids))

    @staticmethod
    def authors_list_from_str(authors_list: str, cast_ids: bool = False) -> typing.List[typing.Union[int, str]]:
        res = authors_list.split("%")
        if cast_ids:
            res = [int(x) for x in res]
        return res

    @classmethod
    def _forum_url(cls, domain: Domain, forum_thread_id: int) -> str:
        res = domain.full_url_template.format(
            path="Guestbook/Messages.aspx",
            args=f"&topic={forum_thread_id}"
        )
        return res

    @property
    def forum_url(self) -> str:
        res = self._forum_url(self.domain, self.forum_thread_id)
        return res

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
        nbsp = u'\xa0'
        game_descr = game_descr or ""
        game_descr = game_descr.replace(nbsp, "").replace("\n\n", "\n").replace("\n \n", "\n")

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
    def _game_details_url(cls, game_id: int):
        res = f'GameDetails.aspx?gid={game_id}'
        return res

    @property
    def game_details_url(self) -> str:
        return self._game_details_url(self.game_id)

    @classmethod
    def _game_details_full_url(cls, domain: Domain, game_id: int) -> str:
        res = domain.full_url_template.format(
            path="GameDetails.aspx",
            args=f"&gid={game_id}"
        )
        return res

    @property
    def game_details_full_url(self) -> str:
        return self._game_details_full_url(self.domain, self.game_id)

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
        last_comment = json["LAST_MESSAGE_TEXT"]

        inst = cls(
            domain,
            json["ID"], json["NAME"], GameMode(json["MODE"]),
            GameFormat(json["FORMAT"]), PassingSequence(json["PASSING_SEQUENCE"]),
            json["START_TIME"], json["END_TIME"],
            ids_, desc,
            cls.authors_list_from_str(json["AUTHORS"]),
            cls.authors_list_from_str(json["AUTHORS_IDS"], True),
            json["FORUM_THREAD_ID"],
            json["LAST_MESSAGE_ID"],
            last_comment,
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

    def _truncate_message(self, limit: int):
        res = self.game_description[:limit]
        if len(self.game_description) > limit:
            res += "..."
        return res

    @property
    def game_description_truncated(self) -> str:
        res = self._truncate_message(MAX_DESCRIPTION_LENGTH)
        return res

    @property
    def game_description_truncated_tg(self) -> str:
        res = self._truncate_message(MAX_DESCRIPTION_LENGTH_TG)
        return res

    @property
    def last_comment_text_truncated(self) -> str:
        if isinstance(self.last_comment_text, str):
            res = self.last_comment_text[:MAX_LAST_MESSAGE_LENGTH]
            if len(self.last_comment_text) > MAX_LAST_MESSAGE_LENGTH:
                res += "..."
        else:
            res = None
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
            "AUTHORS": self.authors_list_str,
            "AUTHORS_IDS": self.authors_ids_list_str,
            "FORUM_THREAD_ID": self.forum_thread_id,
            "LAST_MESSAGE_ID": self.last_comment_id,
            "LAST_MESSAGE_TEXT": self.last_comment_text_truncated,
        }
        return di

    def to_str(self, lang: Language) -> str:
        mem_txt = self.game_format.members_text(lang)
        desc = MENU_LOCALIZATION[MenuItem.DescriptionText][lang]
        game_props = [
            self.game_mode.localized_name(lang),
            self.passing_sequence.localized_name(lang),
            self.game_format.localized_name(lang),
        ]
        time_mod = MENU_LOCALIZATION[MenuItem.TimeFromToText][lang]
        authors_word = MENU_LOCALIZATION[MenuItem.AuthorsText][lang]
        forum_word = MENU_LOCALIZATION[MenuItem.ForumText][lang]
        desc_pts = [
            f"<b>{self.game_name}</b>",
            f"(id <a href='{self.game_details_full_url}' target='_blank'>{int(self.game_id)}</a>)",
            f"[<a href='{self.forum_url}' target='_blank'>{forum_word}</a>]",
        ]
        pts = [
            " ".join(desc_pts),
            f"{authors_word}: {', '.join(self.authors)}",
            "{}, {} ({})".format(*game_props),
            "{} {} {} {}".format(time_mod[0], self.start_time, time_mod[1], self.end_time),
            f"{mem_txt}: {len(self.player_ids)}",
            f"{desc}: {self.game_description_truncated_tg}"
        ]
        res = "\n".join(pts)
        return res

    def __str__(self) -> str:
        res = self.to_str(Language.English)
        return res


class RuleType(enum.Enum):
    Game = ("GameDetails.aspx", "gid={id}")
    Team = ("Teams/TeamDetails.aspx", "tid={id}")
    Player = ("UserDetails.aspx", "uid={id}")
    Author = ("UserDetails.aspx", "uid={id}")

    @classmethod
    def from_attr(cls, attr: str) -> RuleType:
        if attr.endswith("_id"):
            attr = attr[:-3]
        attr = attr.title()
        inst = cls[attr]
        return inst

    def url(self, domain: Domain, id_: int) -> str:
        args = self.value[1].format(id=id_)
        templ = domain.full_url_template.format(
            path=self.value[0],
            args=f"&{args}"
        )
        return templ


@dataclass
class Rule:
    domain: typing.Optional[Domain] = None
    player_id: typing.Optional[int] = None
    team_id: typing.Optional[int] = None
    game_id: typing.Optional[int] = None
    author_id: typing.Optional[int] = None

    @property
    def rule_id(self) -> str:
        to_hash = [
            SALT,
            self.domain or "",
            self.player_id or "",
            self.team_id or "",
            self.game_id or "",
            self.author_id or "",
        ]
        to_hash = "-".join(str(x) for x in to_hash)
        rule_id = hashlib.md5(to_hash.encode()).hexdigest()[:RULE_ID_LENGTH]
        return rule_id

    def to_json(self) -> typing.Dict[str, typing.Any]:
        j = {
            "RULE_ID": self.rule_id,
            "DOMAIN": str(self.domain) if self.domain else None,
            "PLAYER_ID": self.player_id,
            "TEAM_ID": self.team_id,
            "GAME_ID": self.game_id,
            "AUTHOR_ID": self.author_id,
        }
        return j

    @staticmethod
    def _sanitize_value(value: typing.Any):
        if value and not pd.isna(value):
            value = int(value)
        else:
            value = None
        return value

    @classmethod
    def from_json(cls, j: typing.Dict[str, typing.Any]) -> Rule:
        dom = j["DOMAIN"]
        if dom:
            dom = Domain.from_url(dom)

        inst = cls(
            dom,
            cls._sanitize_value(j["PLAYER_ID"]),
            cls._sanitize_value(j["TEAM_ID"]),
            cls._sanitize_value(j["GAME_ID"]),
            cls._sanitize_value(j["AUTHOR_ID"]),
        )
        return inst

    @staticmethod
    def _str_di() -> typing.Dict[str, typing.Dict[Language, str]]:
        di = {
            "player_id": MENU_LOCALIZATION[MenuItem.PlayerIDText],
            "team_id": MENU_LOCALIZATION[MenuItem.TeamIDText],
            "game_id": MENU_LOCALIZATION[MenuItem.GameIDText],
            "author_id": MENU_LOCALIZATION[MenuItem.AuthorIDText],
        }
        return di

    def to_str(self, language: Language, add_href: bool = False) -> str:
        bad_rule = f"Bad rule: " \
                   f"domain={self.domain}, game_id={self.game_id}, " \
                   f"player_id={self.player_id}, team_id={self.team_id}, author_id={self.author_id}"
        nones = [
            an
            for an in ("player_id", "team_id", "game_id", "author_id")
            if getattr(self, an) is not None and not pd.isna(getattr(self, an))
        ]
        assert self.domain is not None and len(nones) <= 1, bad_rule
        di = self._str_di()
        if len(nones) == 1:
            tr = di[nones[0]][language]
            tr = tr.format(id=getattr(self, nones[0]))
            concat = MENU_LOCALIZATION[MenuItem.InDomainText][language]
            pts = [
                tr,
            ]
            pts.extend([
                concat,
                self.domain.name,
            ])
            if add_href:
                rt = RuleType.from_attr(nones[0])
                url = rt.url(self.domain, getattr(self, nones[0]))
                word = MENU_LOCALIZATION[MenuItem.LinkText][language]
                url = f"(<a href={url!r} target='_blank'>{word}</a>)"
                pts.append(url)
        else:
            concat = MENU_LOCALIZATION[MenuItem.DomainText][language]
            if add_href:
                pts = [concat, f"<a href={self.domain.full_url!r} target='_blank'>{self.domain.name}</a>"]
            else:
                pts = [concat, self.domain.full_url]

        if not add_href:
            pts.append(f"[{self.rule_id}]")
        msg = " ".join(pts)
        return msg

    def __str__(self):
        return self.to_str(Language.Russian)


class ChangeType(enum.Enum):
    NewGame = enum.auto()
    NameChanged = enum.auto()
    PassingSequenceChanged = enum.auto()
    StartTimeChanged = enum.auto()
    EndTimeChanged = enum.auto()
    PlayersListChanged = enum.auto()
    DescriptionChanged = enum.auto()
    NewForumMessage = enum.auto()

    @classmethod
    def localization_dict(cls) -> typing.Dict[ChangeType, typing.Dict[Language, str]]:
        di = {
            v: MENU_LOCALIZATION[getattr(MenuItem, n)]
            for n, v in cls.__members__.items()
        }
        return di

    @classmethod
    def to_root_part(cls) -> typing.Dict[ChangeType, str]:
        di = {
            cls.NameChanged: "name",
            cls.PassingSequenceChanged: "passing_sequence",
            cls.StartTimeChanged: "start_time",
            cls.EndTimeChanged: "end_time",
        }
        return di

    def __str__(self) -> str:
        return self.localization_dict()[self][Language.English]


@dataclass
class Change:
    game_new: bool
    name_changed: bool
    passing_sequence_changed: bool
    start_time_changed: bool
    end_time_changed: bool
    players_list_changed: bool
    description_changed: bool
    new_message: bool

    old_name: str
    new_name: str
    old_passing_sequence: PassingSequence
    new_passing_sequence: PassingSequence
    old_start_time: datetime.datetime
    new_start_time: datetime.datetime
    old_end_time: datetime.datetime
    new_end_time: datetime.datetime
    old_player_ids: typing.List[int]
    new_player_ids: typing.List[int]
    old_description_truncated: typing.Optional[str]
    new_description_truncated: typing.Optional[str]
    new_message_text: typing.Optional[str]
    new_last_message_id: typing.Optional[int]

    domain: Domain
    id: int
    game_mode: GameMode
    game_format: GameFormat
    authors: typing.List[str]
    authors_ids: typing.List[int]
    forum_thread_id: int

    @classmethod
    def from_json(cls, j: typing.Dict[str, typing.Any]) -> Change:
        init_dict = {}
        for attr in fields(cls):
            attr: Field
            init_dict[attr.name.lower()] = j[attr.name.upper()]

        if init_dict["old_passing_sequence"] and not pd.isna(init_dict["old_passing_sequence"]):
            init_dict["old_passing_sequence"] = PassingSequence(init_dict["old_passing_sequence"])
        else:
            init_dict["old_passing_sequence"] = PassingSequence.Linear
        if init_dict["new_passing_sequence"] and not pd.isna(init_dict["new_passing_sequence"]):
            init_dict["new_passing_sequence"] = PassingSequence(init_dict["new_passing_sequence"])
        else:
            init_dict["new_passing_sequence"] = PassingSequence.Linear
        if init_dict["old_player_ids"] and not pd.isna(init_dict["old_player_ids"]):
            init_dict["old_player_ids"] = EncounterGame.player_ids_from_string(init_dict["old_player_ids"])
        else:
            init_dict["old_player_ids"] = []

        if init_dict["new_player_ids"] and not pd.isna(init_dict["new_player_ids"]):
            init_dict["new_player_ids"] = EncounterGame.player_ids_from_string(init_dict["new_player_ids"])
        else:
            init_dict["new_player_ids"] = []

        init_dict["game_mode"] = GameMode(init_dict["game_mode"])
        init_dict["game_format"] = GameFormat(init_dict["game_format"])
        init_dict["domain"] = Domain.from_url(init_dict["domain"])
        init_dict["authors"] = EncounterGame.authors_list_from_str(init_dict["authors"])
        init_dict["authors_ids"] = EncounterGame.authors_list_from_str(init_dict["authors_ids"], True)

        if init_dict["forum_thread_id"] is not None:
            init_dict["forum_thread_id"] = int(init_dict["forum_thread_id"])

        inst = cls(**init_dict)
        return inst

    def _to_str_content(self, change_type: ChangeType, language: Language) -> str:
        if change_type is ChangeType.NewGame:
            return EncounterGame(
                self.domain,
                self.id, self.new_name, self.game_mode, self.game_format,
                self.new_passing_sequence, self.new_start_time, self.new_end_time,
                self.new_player_ids, self.new_description_truncated,
                self.authors, self.authors_ids, self.forum_thread_id, self.new_last_message_id,
                self.new_message_text,
            ).to_str(language)

        # TODO: textdiff for description

        default_joiners = ("", " -> ")
        rp = ChangeType.to_root_part()
        if change_type in rp:
            root = rp[change_type]
            if change_type is ChangeType.PassingSequenceChanged:

                if self.old_passing_sequence:
                    old_v_f = self.old_passing_sequence.localized_name(language)
                else:
                    old_v_f = None

                new_v_f = self.new_passing_sequence.localized_name(language)
            else:
                old_v_f = getattr(self, f"old_{root}")
                new_v_f = getattr(self, f"new_{root}")

            interlaced = itertools.chain.from_iterable(zip(default_joiners, [old_v_f, new_v_f]))
            res = " ".join(map(str, interlaced))
            return res
        elif change_type is ChangeType.DescriptionChanged:
            return ""
        elif change_type is ChangeType.PlayersListChanged:
            vals = [
                len(set(self.new_player_ids).difference(self.old_player_ids)),
                len(set(self.old_player_ids).difference(self.new_player_ids)),
                len(self.new_player_ids),
            ]
            joiners = MENU_LOCALIZATION[MenuItem.ChangeParticipantsJoiner][language]
            interlaced = itertools.chain.from_iterable(zip(joiners, vals))
            res = " ".join(map(str, interlaced))
            return res
        else:
            assert change_type is ChangeType.NewForumMessage, "Wrong change type"
            res = str(BeautifulSoup(self.new_message_text, 'lxml').text)
            return res

    def change_type_to_msg(self, change_type: ChangeType, language: Language) -> str:
        prefix = change_type.localization_dict()[change_type][language]
        cont = self._to_str_content(change_type, language)
        msg = f"<u>{prefix}</u>: {cont}"
        return msg

    @property
    def current_changes(self) -> typing.List[ChangeType]:
        change_to_type = [
            (self.name_changed, ChangeType.NameChanged),
            (self.passing_sequence_changed, ChangeType.PassingSequenceChanged),
            (self.start_time_changed, ChangeType.StartTimeChanged),
            (self.end_time_changed, ChangeType.EndTimeChanged),
            (self.players_list_changed, ChangeType.PlayersListChanged),
            (self.new_message, ChangeType.NewForumMessage),
            (self.description_changed, ChangeType.DescriptionChanged),
        ]
        ch = [ct for b, ct in change_to_type if b]
        return ch

    def _to_str_parts(self, language: Language) -> typing.List[str]:
        update_word = MENU_LOCALIZATION[MenuItem.UpdateText][language]
        forum_word = MENU_LOCALIZATION[MenuItem.ForumText][language]
        full_url = EncounterGame._game_details_full_url(self.domain, self.id)
        forum_url = EncounterGame._forum_url(self.domain, self.forum_thread_id)
        prefix_global_pts = [
            update_word,
            f"<b>{self.new_name}</b>",
            f"(id <a href='{full_url}' target='_blank'>{int(self.id)}</a>)",
            f"[<a href='{forum_url}' target='_blank'>{forum_word}</a>]"
        ]
        prefix_global = " ".join(prefix_global_pts)

        res = [prefix_global]

        if self.game_new:
            msg = self.change_type_to_msg(ChangeType.NewGame, language)
            res.append(msg)
            return res

        for change_type in self.current_changes:
            msg = self.change_type_to_msg(change_type, language)
            res.append(msg)

        return res

    def to_str(self, language: Language) -> str:
        pts = self._to_str_parts(language)
        res = "\n".join(pts)
        return res

    def to_json(self) -> typing.Dict[str, typing.Any]:
        chng = str(list(map(str, self.current_changes)))
        res = {
            "DOMAIN": self.domain.full_url,
            "GAME_ID": self.id,
            "CHANGE": chng,
        }
        return res

    def __str__(self):
        return self.to_str(Language.English)


@dataclass
class Update:
    user_id: int
    language: Language
    change: Change
    delivered_ts: datetime.datetime = None

    @staticmethod
    def test_fullpage_screenshot(
            file: str,
            path: str,
            driver: webdriver.Chrome
    ) -> None:
        driver.get(file)
        time.sleep(0.25)
        element = driver.find_element_by_id('main')  # find part of the page you want image of

        driver.set_window_size(800, 100)
        time.sleep(0.25)
        total_height = element.size["height"] + 200
        driver.set_window_size(800, total_height)
        time.sleep(0.25)

        location = element.location
        size = element.size

        png = driver.get_screenshot_as_png()  # saves screenshot of entire page

        im = Image.open(BytesIO(png))  # uses PIL library to open image in memory

        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

        im = im.crop((left, top, right, bottom))  # defines crop points
        im.save(path)  # saves new cropped image
        return None

    @classmethod
    def create_diff(
            cls,
            old_description: str, new_description: str, lang: Language,
            driver: webdriver.Chrome,
    ) -> typing.Tuple[typing.Any, str]:
        names = MENU_LOCALIZATION[MenuItem.DescriptionBeforeAfter][lang]
        res = html_diffs(old_description, new_description, *names)
        html_fd, html_path = tempfile.mkstemp(suffix=".html")
        pic_fd, pic_path = tempfile.mkstemp(suffix=".png")
        with open(html_path, 'w') as tmp:
            tmp.write(res)
        try:
            cls.test_fullpage_screenshot(f"file://{html_path}", pic_path, driver)
        finally:
            os.close(html_fd)
            os.remove(html_path)
        return pic_fd, pic_path

    @property
    def msg(self) -> str:
        msg_ = self.change.to_str(self.language)
        return msg_

    @property
    def has_diffpic(self) -> bool:
        return ChangeType.DescriptionChanged in self.change.current_changes

    @contextmanager
    def diffpic(self, driver: webdriver.Chrome):
        pic_fd, pic_path = self.create_diff(
            self.change.old_description_truncated or "",
            self.change.new_description_truncated or "",
            lang=self.language,
            driver=driver,
        )
        try:
            with open(pic_path, "rb") as pic:
                yield pic
        finally:
            os.close(pic_fd)
            os.remove(pic_path)
        return None

    @classmethod
    def from_row(
            cls,
            row: pd.Series,
    ) -> Update:
        user_id = row["USER_ID"]
        lang = Language(row["LANGUAGE"])
        # noinspection PyTypeChecker
        change = Change.from_json(row.to_dict())
        inst = cls(
            user_id, lang, change
        )
        return inst

    def to_json(self) -> typing.Dict[str, typing.Any]:
        res = {
            "USER_ID": self.user_id,
            **self.change.to_json(),
            "DELIVERED": self.delivered_ts,
        }
        return res


if __name__ == '__main__':
    # games_ = Domain.from_url("http://kramatorsk.en.cx").get_games()
    games_ = Domain.from_url("http://kharkiv.en.cx/?lang=ru")
    res_ = games_.get_games()
    print(res_)

    # print(GameFormat.localization_dict())

    # print(Domain.from_url("krak.en.cx/?lang=dido"))
    # print(list(map(str, games_)))
    # print("a")
    # print(GameMode(1))
    # print(PassingSequence.from_str("Linear"))
    # print(PassingSequence.from_str("Линейная"))
    # print(GameFormat.from_str("Командами"))
    # print(GameFormat.from_str("Team"))
    # print(GameFormat.from_str("Storm"))
