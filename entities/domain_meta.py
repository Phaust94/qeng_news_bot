
from __future__ import annotations

import enum
import typing

if typing.TYPE_CHECKING:
    from entities.game import BaseGame
    from entities.domain import Domain

__all__ = [
    "UpperLevelDomain",
]


class UpperLevelDomain(enum.Enum):
    EN_CX = enum.auto()
    QUEST_UA = enum.auto()
    QENG = enum.auto()

    @classmethod
    def regex_list(cls) -> typing.List[typing.Tuple[UpperLevelDomain, str]]:
        res = [
            (cls.EN_CX, r"([a-zA-Z0-9]+?)\.en\.cx"),
            (cls.QUEST_UA, r"([a-zA-Z0-9]+?)\.quest\.ua"),
            (cls.QENG, r"([a-zA-Z0-9]+?)\.qeng\.org"),
            (cls.QUEST_UA, r"()quest\.ua")
        ]
        return res

    @property
    def domain_class(self) -> type(Domain):
        # To avoid circular imports
        from entities.encounter_domain import EncounterDomain
        from entities.qeng_domain import QEngDomain

        cls = self.__class__

        res = {
            cls.QENG: QEngDomain,
            cls.EN_CX: EncounterDomain,
            cls.QUEST_UA: EncounterDomain,
        }[self]
        return res

    @property
    def game_class(self) -> type(BaseGame):
        # To avoid circular imports
        from entities.encounter_domain import EncounterGame
        from entities.qeng_domain import QEngGame

        cls = self.__class__

        res = {
            cls.QENG: QEngGame,
            cls.EN_CX: EncounterGame,
            cls.QUEST_UA: EncounterGame,
        }[self]
        return res

    def __str__(self) -> str:
        res = {
            self.__class__.QUEST_UA: "quest.ua",
            self.__class__.EN_CX: "en.cx",
            self.__class__.QENG: "qeng.org",
        }
        s = res[self]
        return s


if __name__ == '__main__':
    print(UpperLevelDomain.QENG.domain_class())
    print(UpperLevelDomain.EN_CX.domain_class())
    print(UpperLevelDomain.QUEST_UA.domain_class())
