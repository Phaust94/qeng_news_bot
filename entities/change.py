"""

"""

from __future__ import annotations

import datetime
import itertools
from dataclasses import dataclass, fields, Field
import enum
import typing

import pandas as pd
# noinspection PyProtectedMember
from bs4 import BeautifulSoup

from translations import Language, MenuItem, MENU_LOCALIZATION
from entities.game_attrs import PassingSequence, GameFormat, GameMode
from entities.domain import Domain
from entities.game import BaseGame
from entities.rule import RuleType


__all__ = [
    "Change", "ChangeType",
]

TIME_UNITS = [
    (MenuItem.TUYears, 365 * 24 * 60 * 60),
    (MenuItem.TUMonths, 30 * 24 * 60 * 60),
    (MenuItem.TUDays, 24 * 60 * 60),
    (MenuItem.TUHours, 60 * 60),
    (MenuItem.TUMinutes, 60),
    (MenuItem.TUSeconds, 1),
]


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
            init_dict["old_player_ids"] = BaseGame.player_ids_from_string(init_dict["old_player_ids"])
        else:
            init_dict["old_player_ids"] = []

        if init_dict["new_player_ids"] and not pd.isna(init_dict["new_player_ids"]):
            init_dict["new_player_ids"] = BaseGame.player_ids_from_string(init_dict["new_player_ids"])
        else:
            init_dict["new_player_ids"] = []

        init_dict["game_mode"] = GameMode(init_dict["game_mode"])
        init_dict["game_format"] = GameFormat(init_dict["game_format"])
        init_dict["domain"] = Domain.from_url(init_dict["domain"])
        init_dict["authors"] = BaseGame.authors_list_from_str(init_dict["authors"])
        init_dict["authors_ids"] = BaseGame.authors_list_from_str(init_dict["authors_ids"], True)

        if pd.isna(init_dict["forum_thread_id"]):
            init_dict["forum_thread_id"] = None

        if pd.isna(init_dict["new_message_text"]):
            init_dict["new_message_text"] = None

        if init_dict["forum_thread_id"] is not None:
            init_dict["forum_thread_id"] = int(init_dict["forum_thread_id"])

        for time in [
            "new_start_time", "old_start_time", "new_end_time", "old_end_time",
        ]:
            if isinstance(init_dict[time], str):
                init_dict[time] = datetime.datetime.strptime(init_dict[time], '%Y-%m-%d %H:%M:%S')

        inst = cls(**init_dict)
        return inst

    def change_delta_word(self, time_type: str, language: Language) -> str:
        delta = getattr(self, f"new_{time_type}") - getattr(self, f"old_{time_type}")
        seconds = delta.total_seconds()
        sign = 1 if seconds > 0 else -1
        seconds = abs(seconds)
        pts = [MenuItem.TUBy]
        for word, unit in TIME_UNITS:
            if seconds >= unit:
                n_whole = seconds // unit
                seconds -= n_whole * unit
                pts.extend([int(n_whole), word])

        dir_word = MenuItem.TUForward if sign == 1 else MenuItem.TUBackward
        pts.append(dir_word)
        pts = [
            str(p) if not isinstance(p, MenuItem) else MENU_LOCALIZATION[p][language]
            for p in pts
        ]
        res = "({})".format(" ".join(pts))
        return res

    def _to_str_content(self, change_type: ChangeType, language: Language) -> str:
        if change_type is ChangeType.NewGame:
            game_cls = self.domain.upper_level_domain.game_class
            inst = game_cls(
                self.domain,
                self.id, self.new_name, self.game_mode, self.game_format,
                self.new_passing_sequence, self.new_start_time, self.new_end_time,
                self.new_player_ids, self.new_description_truncated,
                self.authors, self.authors_ids, self.forum_thread_id, self.new_last_message_id,
                self.new_message_text,
            )
            msg = inst.to_str(language)
            return msg

        default_joiners = ("\n", " -> ")
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

            interlaced = list(itertools.chain.from_iterable(zip(default_joiners, [old_v_f, new_v_f])))
            if change_type is ChangeType.StartTimeChanged:
                interlaced.append(
                    self.change_delta_word("start_time", language)
                )
            if change_type is ChangeType.EndTimeChanged:
                interlaced.append(
                    self.change_delta_word("end_time", language)
                )

            res = " ".join(map(str, interlaced))
            return res
        elif change_type is ChangeType.DescriptionChanged:
            return ""
        elif change_type is ChangeType.PlayersListChanged:
            new_players = sorted(set(self.new_player_ids).difference(self.old_player_ids))
            url_templ_func = RuleType.from_game_format(self.game_format)
            new_players_urls = [
                f"<a href='{url_templ_func.url(self.domain, pl)}'>#{i + 1}</a>"
                for i, pl in enumerate(new_players)
            ]
            new_players_urls = f"({', '.join(new_players_urls)})" if new_players_urls else ''

            dropped_players = sorted(set(self.old_player_ids).difference(self.new_player_ids))
            dropped_players_urls = [
                f"<a href='{url_templ_func.url(self.domain, pl)}'>#{i + 1}</a>"
                for i, pl in enumerate(dropped_players)
            ]
            dropped_players_urls = f"({', '.join(dropped_players_urls)})" if dropped_players_urls else ''

            vals = [
                dict(n_new=len(new_players), new=new_players_urls),
                dict(n_dropped=len(dropped_players), dropped=dropped_players_urls),
                dict(tot=len(self.new_player_ids)),
            ]
            joiners = MENU_LOCALIZATION[MenuItem.ChangeParticipantsJoiner][language]
            interlaced = [
                j.format(**v)
                for j, v in zip(joiners, vals)
            ]
            res = "\n" + "\n".join(map(str, interlaced))
            return res
        else:
            assert change_type is ChangeType.NewForumMessage, "Wrong change type"
            res = str(BeautifulSoup(self.new_message_text or '', 'lxml').text)
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
        game_cls = self.domain.upper_level_domain.game_class
        # noinspection PyProtectedMember
        full_url = game_cls._game_details_full_url(self.domain, self.id)
        prefix_global_pts = [
            update_word,
            f"<b>{self.new_name}</b>",
            f"(id <a href='{full_url}' target='_blank'>{int(self.id)}</a>)",
        ]
        if self.forum_thread_id is not None:
            # noinspection PyProtectedMember
            forum_url = game_cls._forum_url(self.domain, self.forum_thread_id)
            prefix_global_pts.append(f"[<a href='{forum_url}' target='_blank'>{forum_word}</a>]")

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
