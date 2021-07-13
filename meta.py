"""

"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, fields, Field
import re
import enum
import typing
import hashlib
from urllib.parse import urlsplit, parse_qs

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
import feedparser

from constants import MAX_DESCRIPTION_LENGTH, MAX_DESCRIPTION_LENGTH_TG, MAX_LAST_MESSAGE_LENGTH,\
    SALT, RULE_ID_LENGTH

__all__ = [
    "Domain", "EncounterGame", "Rule",
    "GameMode", "GameFormat", "PassingSequence",
    "Language",
]


DOMAIN_REGEX = r"([a-zA-Z0-9]+?)\.en\.cx"
# LANGUAGE_REGEX = r"\?.*?lang=([a-zA-Z])"

CHROME_DEFAULT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'"
USER_AGENTS_FACTORY = UserAgent(fallback=CHROME_DEFAULT)


class Language(enum.Enum):
    Russian = enum.auto()
    English = enum.auto()
    DemoEnglish = enum.auto()

    @classmethod
    def _flag_dict(cls) -> typing.Dict[Language, str]:
        res = {
            cls.English: "🇬🇧",
            cls.Russian: "🇷🇺",
        }
        return res

    @property
    def flag(self) -> typing.Union[str, None]:
        res = self._flag_dict().get(self)
        return res

    @classmethod
    def from_flag(cls, flag: str) -> Language:
        inv_flag_dict = {
            v: k
            for k, v in cls._flag_dict().items()
        }
        inst = inv_flag_dict[flag]
        return inst

    @classmethod
    def _str_dict(cls) -> typing.Dict[Language, str]:
        res = {
            cls.English: "en",
            cls.Russian: "ru",
        }
        return res

    def to_str(self) -> str:
        res = self._str_dict()[self]
        return res

    @classmethod
    def from_str(cls, s: str) -> Language:
        inv_di = {
            v: k
            for k, v in cls._str_dict().items()
        }
        inv_di[""] = Language.Russian
        inst = inv_di[s]
        return inst

    @classmethod
    def full_name_dict(cls) -> typing.Dict[Language, str]:
        di = {
            cls.English: "English",
            cls.Russian: "Русский",
        }
        return di

    @classmethod
    def from_full_name(cls, full_name: str) -> Language:
        inv_di = {
            v: k
            for k, v in cls.full_name_dict().items()
        }
        inst = inv_di.get(full_name, cls.English)
        return inst

    @property
    def full_name(self) -> str:
        return self.full_name_dict()[self]


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
                Language.DemoEnglish: "Real",
            },
            cls.Points: {
                Language.Russian: "Точки",
                Language.English: "Points",
            },
            cls.Brainstorm: {
                Language.Russian: "Мозговой штурм",
                Language.English: "Brainstorm",
                Language.DemoEnglish: "Brainstorming",
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
    Personal = enum.auto()

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
            cls.Personal: {
                Language.Russian: "Персонально",
                Language.English: "Personal",
                Language.DemoEnglish: "Personal(she)",
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
    def localization_dict(cls) -> typing.Dict[PassingSequence, typing.Dict[Language, str]]:
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
                Language.English: "Custom (not linear)",
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
    authors: typing.List[str]
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
    def _parse_time(time: str) -> datetime.datetime:
        # noinspection PyBroadException
        try:
            dt = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        except Exception:
            # noinspection PyBroadException
            try:
                d, t = time.split(" ")[:2]
                d = d[:10]
                if t.endswith("("):
                    t = t[:-2]
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

    @property
    def authors_list_str(self) -> str:
        return "%".join(self.authors)

    @staticmethod
    def authors_list_from_str(authors_list: str) -> typing.List[str]:
        return authors_list.split("%")

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
        is_judged = game_mode in {GameMode.Competition, GameMode.PhotoHunt, GameMode.PhotoExtreme}
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
        game_descr = game_descr.replace(nbsp, "").replace("\n\n", "\n").replace("\n \n", "\n")

        authors = [
            el.text
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
            authors, tid,
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
        # if json["DESCRIPTION_REAL_LENGTH"] > MAX_DESCRIPTION_LENGTH and desc.endswith("..."):
        #     desc = desc[:-3]

        last_comment = json["LAST_MESSAGE_TEXT"]
        # if len(last_comment) > MAX_LAST_MESSAGE_LENGTH:
        #     last_comment = last_comment[:-3]

        inst = cls(
            domain,
            json["ID"], json["NAME"], GameMode(json["MODE"]),
            GameFormat(json["FORMAT"]), PassingSequence(json["PASSING_SEQUENCE"]),
            json["START_TIME"], json["END_TIME"],
            ids_, desc,
            cls.authors_list_from_str(json["AUTHORS"]),
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
            "FORUM_THREAD_ID": self.forum_thread_id,
            "LAST_MESSAGE_ID": self.last_comment_id,
            "LAST_MESSAGE_TEXT": self.last_comment_text_truncated,
        }
        return di

    def to_str(self, lang: Language) -> str:
        mem_txt = self.game_format.members_text(lang)
        desc = {
            Language.Russian: "Описание",
            Language.English: "Description",
        }[lang]
        game_props = [
            self.game_mode.localized_name(lang),
            self.passing_sequence.localized_name(lang),
            self.game_format.localized_name(lang),
        ]
        time_mod = {
            Language.Russian: ["С", "по"],
            Language.English: ["From", "to"],
        }[lang]
        authors_word = {
            Language.Russian: "Автор(ы)",
            Language.English: "Author(s)",
        }[lang]
        forum_word = {
            Language.Russian: "Форум",
            Language.English: "Forum",
        }[lang]
        desc_pts = [
            f"<b>{self.game_name}</b>",
            f"(id <a href='{self.game_details_full_url}' target='_blank'>{int(self.game_id)}</a>)",
            f"[<a href='{self.forum_url}' target='_blank'>{forum_word}</a>]",
        ]
        pts = [
            " ".join(desc_pts),
            f"{authors_word}: {','.join(self.authors)}",
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

    @property
    def rule_id(self) -> str:
        to_hash = [
            SALT,
            self.domain or "",
            self.player_id or "",
            self.team_id or "",
            self.game_id or "",
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
        )
        return inst

    def _str_di(self) -> typing.Dict[str, typing.Dict[Language, str]]:
        di = {
            "player_id": {
                Language.Russian: f"Игрок {self.player_id}",
                Language.English: f"Player {self.player_id}",
            },
            "team_id": {
                Language.Russian: f"Команда {self.team_id}",
                Language.English: f"Team {self.team_id}",
            },
            "game_id": {
                Language.Russian: f"Игра {self.game_id}",
                Language.English: f"Game {self.game_id})",
            },
        }
        return di

    def to_str(self, language: Language, add_href: bool = False) -> str:
        bad_rule = f"Bad rule: " \
                   f"domain={self.domain}, game_id={self.game_id}, player_id={self.player_id}, team_id={self.team_id}"
        nones = [
            an
            for an in ("player_id", "team_id", "game_id")
            if getattr(self, an) is not None and not pd.isna(getattr(self, an))
        ]
        assert self.domain is not None and len(nones) <= 1, bad_rule
        di = self._str_di()
        if len(nones) == 1:
            tr = di[nones[0]][language]
            concat = {
                Language.Russian: "в домене",
                Language.English: "in domain",
            }[language]
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
                word = {
                    Language.Russian: "ссылка",
                    Language.English: "link",
                }[language]
                url = f"(<a href={url!r} target='_blank'>{word}</a>)"
                pts.append(url)
        else:
            concat = {
                Language.Russian: "Домен",
                Language.English: "Domain",
            }[language]
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
            cls.NewGame: {
                Language.Russian: "Новая игра",
                Language.English: "New game",
            },
            cls.NameChanged: {
                Language.Russian: "Название игры изменилось",
                Language.English: "Game name changed",
            },
            cls.StartTimeChanged: {
                Language.Russian: "Начало игры перенесено",
                Language.English: "Game start time changed",
            },
            cls.EndTimeChanged: {
                Language.Russian: "Окончание игры перенесено",
                Language.English: "Game end time changed",
            },
            cls.PassingSequenceChanged: {
                Language.Russian: "Последовательность прохождения игры изменилась",
                Language.English: "Game passing sequence changed",
            },
            cls.PlayersListChanged: {
                Language.Russian: "Список участников изменился",
                Language.English: "Playsers list changed",
            },
            cls.DescriptionChanged: {
                Language.Russian: "Описание игры изменилось",
                Language.English: "Game description changed",
            },
            cls.NewForumMessage: {
                Language.Russian: "Новое сообщение(я) на форуме. Последнее сообщение",
                Language.English: "New forum message(ы). Last message",
            }
        }
        return di

    @classmethod
    def to_root_part(cls) -> typing.Dict[ChangeType, str]:
        di = {
            cls.NameChanged: "name",
            cls.PassingSequenceChanged: "passing_sequence",
            cls.StartTimeChanged: "start_time",
            cls.EndTimeChanged: "end_time",
            cls.PlayersListChanged: "player_ids",
            cls.DescriptionChanged: "description_truncated",
        }
        return di


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
    old_description_truncated: str
    new_description_truncated: str
    new_message_text: typing.Optional[str]
    new_last_message_id: typing.Optional[int]

    domain: Domain
    id: int
    game_mode: GameMode
    game_format: GameFormat
    authors: typing.List[str]
    forum_thread_id: int

    @classmethod
    def from_json(cls, j: typing.Dict[str, typing.Any]) -> Change:
        init_dict = {}
        for attr in fields(cls):
            attr: Field
            init_dict[attr.name.lower()] = j[attr.name.upper()]

        if init_dict["old_passing_sequence"]:
            init_dict["old_passing_sequence"] = PassingSequence(init_dict["old_passing_sequence"])
        init_dict["new_passing_sequence"] = PassingSequence(init_dict["new_passing_sequence"])
        if init_dict["old_player_ids"]:
            init_dict["old_player_ids"] = EncounterGame.player_ids_from_string(init_dict["old_player_ids"])
        init_dict["new_player_ids"] = EncounterGame.player_ids_from_string(init_dict["new_player_ids"])
        init_dict["game_mode"] = GameMode(init_dict["game_mode"])
        init_dict["game_format"] = GameFormat(init_dict["game_format"])
        init_dict["domain"] = Domain.from_url(init_dict["domain"])
        init_dict["authors"] = EncounterGame.authors_list_from_str(init_dict["authors"])

        if init_dict["forum_thread_id"] is not None:
            init_dict["forum_thread_id"] = int(init_dict["forum_thread_id"])

        inst = cls(**init_dict)
        return inst

    def _to_str_content(self, language: Language) -> typing.Dict[ChangeType, str]:
        di = {
            ChangeType.NewGame: EncounterGame(
                self.domain,
                self.id, self.new_name, self.game_mode, self.game_format,
                self.new_passing_sequence, self.new_start_time, self.new_end_time,
                self.new_player_ids, self.new_description_truncated,
                self.authors, self.forum_thread_id, self.new_last_message_id,
                self.new_message_text,
            ).to_str(language),
        }
        # TODO: textdiff for description

        joiners = {
            ChangeType.DescriptionChanged: {
                Language.Russian: ("Было:\n", "\nСтало:\n"),
                Language.English: ("Before:\n", "\nNow:\n"),
            },
            ChangeType.PlayersListChanged: {
                Language.Russian: ("\nНовых заявок: ", "\nСняли заявку: "),
                Language.English: ("\nNew participants: ", "\nDismissed participants: "),
            }
        }
        default_joiners = {
            Language.Russian: ("", " -> "),
            Language.English: ("", " -> "),
        }

        for ct, root in ChangeType.to_root_part().items():
            if ct is ChangeType.PassingSequenceChanged:
                if self.old_passing_sequence:
                    old_v_f = self.old_passing_sequence.localized_name(language)
                else:
                    old_v_f = None
                new_v_f = self.new_passing_sequence.localized_name(language)
            elif ct is ChangeType.PlayersListChanged:
                old_v_f = str(len(set(self.new_player_ids).difference(self.old_player_ids)))
                new_v_f = str(len(set(self.old_player_ids).difference(self.new_player_ids)))
            else:
                old_v_f = getattr(self, f"old_{root}")
                new_v_f = getattr(self, f"new_{root}")

            joiners_curr = joiners.get(ct, default_joiners)[language]
            di[ct] = " ".join([
                joiners_curr[0], old_v_f, joiners_curr[1], new_v_f
            ])

        di[ChangeType.NewForumMessage] = BeautifulSoup(self.new_message_text, 'lxml').text

        return di

    def change_type_to_msg(self, change_type: ChangeType, language: Language) -> str:
        prefix = change_type.localization_dict()[change_type][language]
        cont_dict = self._to_str_content(language)
        cont = cont_dict[change_type]
        msg = f"{prefix}: {cont}"
        return msg

    def _to_str_parts(self, language: Language) -> typing.List[str]:
        update_word = {
            Language.Russian: "Обновление по игре",
            Language.English: "Game update for"
        }[language]
        forum_word = {
            Language.Russian: "Форум",
            Language.English: "Forum",
        }[language]
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

        change_to_type = [
            (self.name_changed, ChangeType.NameChanged),
            (self.passing_sequence_changed, ChangeType.PassingSequenceChanged),
            (self.start_time_changed, ChangeType.StartTimeChanged),
            (self.end_time_changed, ChangeType.EndTimeChanged),
            (self.description_changed, ChangeType.DescriptionChanged),
            (self.players_list_changed, ChangeType.PlayersListChanged),
            (self.new_message, ChangeType.NewForumMessage),
        ]

        for change_bool, change_type in change_to_type:
            if change_bool:
                msg = self.change_type_to_msg(change_type, language)
                res.append(msg)

        return res

    def to_str(self, language: Language) -> str:
        pts = self._to_str_parts(language)
        res = "\n".join(pts)
        return res

    def __str__(self):
        return self.to_str(Language.English)


if __name__ == '__main__':
    # games_ = Domain.from_url("http://kramatorsk.en.cx").get_games()
    games_ = Domain.from_url("http://kharkiv.en.cx/?lang=ru")
    games_.get_games()
    # print(Domain.from_url("krak.en.cx/?lang=dido"))
    # print(list(map(str, games_)))
    # print("a")
    # print(GameMode(1))
    # print(PassingSequence.from_str("Linear"))
    # print(PassingSequence.from_str("Линейная"))
    # print(GameFormat.from_str("Командами"))
    # print(GameFormat.from_str("Team"))
    # print(GameFormat.from_str("Storm"))
