
from __future__ import annotations

import abc
from dataclasses import dataclass
import re
import typing
from urllib.parse import urlsplit, parse_qs

from entities.domain_meta import UpperLevelDomain
from translations import Language

if typing.TYPE_CHECKING:
    from entities.game import BaseGame

__all__ = [
    "Domain",
]


@dataclass
class Domain(abc.ABC):
    name: str
    language: Language = Language.Russian
    is_https: bool = False
    upper_level_domain: UpperLevelDomain = UpperLevelDomain.EN_CX

    @property
    def pretty_name(self) -> str:
        res = [self.name, str(self.upper_level_domain)]
        res = [x for x in res if x]
        res = ".".join(res)
        return res

    @property
    def pretty_href_name(self) -> str:
        res = f"<a href={self.full_url!r} target='_blank'>{self.pretty_name}</a>"
        return res

    @property
    def base_url(self) -> str:
        letter = "s" if self.is_https else ""
        pts = [self.name, str(self.upper_level_domain)]
        pts = [x for x in pts if x]
        host = ".".join(pts)
        res = f"http{letter}://{host}"
        return res

    @property
    def full_url(self) -> str:
        raise NotImplementedError()

    @property
    def full_url_template(self) -> str:
        raise NotImplementedError()

    @property
    def full_url_to_parse(self) -> str:
        raise NotImplementedError()

    @property
    def forum_url(self) -> typing.Optional[str]:
        raise NotImplementedError()

    @classmethod
    def from_url(cls, url: str) -> Domain:
        url = url.lower()
        if not url.startswith("http"):
            url = f"http://{url}"
        sp = urlsplit(url)
        is_https = sp.scheme == 'https'
        params = parse_qs(sp.query)
        lang = params.get("lang", [''])[0]

        for upper_level_domain, dom_reg in UpperLevelDomain.regex_list():
            dom_pt = re.findall(dom_reg, sp.netloc)
            if dom_pt:
                dom = dom_pt[0]
                break
        else:
            raise IndexError(f"Incorrect URL: {url}")

        if dom.startswith("m."):
            dom = dom[2:]

        if upper_level_domain is UpperLevelDomain.QENG:
            is_https = True

        lang = Language.from_str(lang)
        cls_ = upper_level_domain.domain_class
        inst = cls_(dom, lang, is_https, upper_level_domain)
        return inst

    def get_games(self) -> typing.List[BaseGame]:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.full_url


if __name__ == '__main__':
    for dom_ in [
        # "od.quest.ua", "kharkiv.en.cx", "quest.ua", "game.qeng.org",
        "game.qeng.org",
    ]:
        dom_inst_ = Domain.from_url(dom_)
        print(dom_inst_, dom_inst_.full_url_to_parse)
        games_ = dom_inst_.get_games()
        print(games_)
