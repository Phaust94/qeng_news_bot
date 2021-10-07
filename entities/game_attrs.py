
from __future__ import annotations

import enum
import typing

from translations import Language, MenuItem, MENU_LOCALIZATION

__all__ = [
    "GameMode", "GameFormat", "PassingSequence",
]


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


class GameFormat(CustomNamedEnum):
    Single = enum.auto()
    Team = enum.auto()
    Personal = enum.auto()

    @classmethod
    def _default_value(cls) -> GameFormat:
        return cls.Single

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
