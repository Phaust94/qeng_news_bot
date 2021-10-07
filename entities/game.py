"""

"""

from __future__ import annotations

import abc
import datetime
from dataclasses import dataclass
import re
import typing

import pandas as pd
# noinspection PyProtectedMember
from bs4 import Tag

from meta_constants import MAX_DESCRIPTION_LENGTH, MAX_DESCRIPTION_LENGTH_TG, MAX_LAST_MESSAGE_LENGTH
from translations import Language, MenuItem, MENU_LOCALIZATION
from entities.domain import Domain
from entities.game_attrs import GameMode, GameFormat, PassingSequence

__all__ = [
    "BaseGame",
]


@dataclass
class BaseGame(abc.ABC):
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
    forum_thread_id: typing.Optional[int]
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

    @property
    def authors_list_str(self) -> str:
        return "%".join(self.authors)

    @property
    def authors_ids_list_str(self) -> str:
        return "%".join(map(str, self.author_ids))

    @staticmethod
    def authors_list_from_str(authors_list: str, cast_ids: bool = False) -> typing.List[typing.Union[int, str]]:
        if authors_list:
            res = authors_list.split("%")
        else:
            res = []
        if cast_ids:
            res = [int(x) for x in res]
        return res

    @staticmethod
    def strip_description_text(game_descr: str):
        nbsp = u'\xa0'
        game_descr = game_descr or ""
        game_descr = game_descr.replace(nbsp, "").replace("\n\n", "\n").replace("\n \n", "\n")
        return game_descr

    @classmethod
    def _forum_url(cls, domain: Domain, forum_thread_id: int) -> typing.Optional[str]:
        raise NotImplementedError()

    @property
    def forum_url(self) -> typing.Optional[str]:
        res = self._forum_url(self.domain, self.forum_thread_id)
        return res

    @classmethod
    def _game_details_full_url(cls, domain: Domain, game_id: int) -> str:
        raise NotImplementedError()

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
    ) -> BaseGame:
        ids_ = cls.player_ids_from_string(json["PLAYER_IDS"])
        domain = Domain.from_url(json["DOMAIN"])

        desc = json["DESCRIPTION_TRUNCATED"]
        last_comment = json["LAST_MESSAGE_TEXT"]

        cls_ = domain.upper_level_domain.game_class

        inst = cls_(
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
        desc_pts = [
            f"<b>{self.game_name}</b>",
            f"(id <a href='{self.game_details_full_url}' target='_blank'>{int(self.game_id)}</a>)",
        ]
        if self.forum_url:
            forum_word = MENU_LOCALIZATION[MenuItem.ForumText][lang]
            desc_pts.append(f"[<a href='{self.forum_url}' target='_blank'>{forum_word}</a>]")

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
