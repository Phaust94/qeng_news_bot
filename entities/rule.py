
from __future__ import annotations

from dataclasses import dataclass
import enum
import typing
import hashlib

import pandas as pd

from meta_constants import SALT, RULE_ID_LENGTH
from translations import Language, MenuItem, MENU_LOCALIZATION
from entities.domain import Domain
from entities.game_attrs import GameFormat


__all__ = [
    "Rule", "RuleType",
]


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

    @classmethod
    def from_game_format(cls, game_format: GameFormat) -> RuleType:
        di = {
            game_format.Single: cls.Player,
            game_format.Personal: cls.Player,
            game_format.Team: cls.Team,
        }
        inst = di[game_format]
        return inst


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

    def to_str(
        self,
        language: Language,
        add_href: bool = False,
        force_no_href: bool = False,
    ) -> str:
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
                self.domain.pretty_href_name if not force_no_href else self.domain.pretty_name,
            ])
            if add_href:
                rt = RuleType.from_attr(nones[0])
                url = rt.url(self.domain, getattr(self, nones[0]))
                word = MENU_LOCALIZATION[MenuItem.LinkText][language]
                url = f"(<a href={url!r} target='_blank'>{word}</a>)"
                pts.append(url)
        else:
            concat = MENU_LOCALIZATION[MenuItem.DomainText][language]
            if not force_no_href:
                pts = [concat, self.domain.pretty_href_name]
            else:
                pts = [concat, self.domain.pretty_name]

        if not add_href:
            pts.append(f"[{self.rule_id}]")
        msg = " ".join(pts)
        return msg

    def __str__(self):
        return self.to_str(Language.Russian)
