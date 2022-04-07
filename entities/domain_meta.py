
from __future__ import annotations

import enum
import typing

if typing.TYPE_CHECKING:
    from entities.game import BaseGame
    from entities.domain import Domain

__all__ = [
    "UpperLevelDomain",
    "WHITELISTED_IP_TO_ENGINE",
]


class UpperLevelDomain(enum.Enum):
    QENG = enum.auto()

    @classmethod
    def regex_list(cls) -> typing.List[typing.Tuple[UpperLevelDomain, str]]:
        res = [
            (cls.QENG, r"([a-zA-Z0-9]+?)\.qeng\.org"),
        ]
        return res

    @property
    def domain_class(self) -> type(Domain):
        # To avoid circular imports
        from entities.qeng_domain import QEngDomain

        cls = self.__class__

        res = {
            cls.QENG: QEngDomain,
        }[self]
        return res

    @property
    def game_class(self) -> type(BaseGame):
        # To avoid circular imports
        from entities.qeng_domain import QEngGame

        cls = self.__class__

        res = {
            cls.QENG: QEngGame,
        }[self]
        return res

    def __str__(self) -> str:
        res = {
            self.__class__.QENG: "qeng.org",
        }
        s = res[self]
        return s


WHITELISTED_IP_TO_ENGINE = {
    '88.80.184.82': UpperLevelDomain.QENG,
}


if __name__ == '__main__':
    print(UpperLevelDomain.QENG.domain_class())
