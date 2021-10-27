
from __future__ import annotations

import abc
from dataclasses import dataclass
import re
import typing
import socket
from urllib.parse import urlsplit, parse_qs
import datetime

from cachier import cachier

from entities.domain_meta import UpperLevelDomain, WHITELISTED_IP_TO_ENGINE
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
    force_add_upper_level_postfix: bool = True

    @property
    def pretty_name(self) -> str:
        res = [self.name]
        if self.force_add_upper_level_postfix:
            res.append(str(self.upper_level_domain))
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
        res = f"http{letter}://{self.pretty_name}"
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
        force_add_postfix = True

        for upper_level_domain, dom_reg in UpperLevelDomain.regex_list():
            dom_pt = re.findall(dom_reg, sp.netloc)
            if dom_pt:
                dom = dom_pt[0]
                break
        else:
            # noinspection PyBroadException
            try:
                domain_ip = cls.get_ip(sp.netloc)
            except Exception:
                domain_ip = {}
            inters = domain_ip.intersection(WHITELISTED_IP_TO_ENGINE)
            inters_domains = {WHITELISTED_IP_TO_ENGINE[el] for el in inters}

            if len(set(inters_domains)) != 1:
                raise IndexError(f"Incorrect URL: {url}")

            upper_level_domain = inters_domains.pop()
            dom = sp.netloc
            force_add_postfix = False

        if dom.startswith("m."):
            dom = dom[2:]

        if upper_level_domain is UpperLevelDomain.QENG:
            is_https = True

        lang = Language.from_str(lang)
        cls_ = upper_level_domain.domain_class
        inst = cls_(
            dom, lang,
            is_https, upper_level_domain,
            force_add_upper_level_postfix=force_add_postfix
        )
        return inst

    def get_games(self) -> typing.List[BaseGame]:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.full_url

    @property
    def game_details_url(self) -> typing.Tuple[str, str]:
        raise NotImplementedError()

    @property
    def team_details_url(self) -> typing.Tuple[str, str]:
        raise NotImplementedError()

    @property
    def user_details_url(self) -> typing.Tuple[str, str]:
        raise NotImplementedError()

    @staticmethod
    @cachier(stale_after=datetime.timedelta(days=14))
    def get_ip(site: str) -> typing.Set[str]:
        site = site.lower()
        sp = urlsplit(site)
        if sp.netloc:
            site = sp.netloc
        else:
            site = sp.path
        ip_list = []
        ais = socket.getaddrinfo(site, 0, 0, 0, 0)
        for result in ais:
            ip_list.append(result[-1][0])
        ip_list = set(ip_list)
        return ip_list


if __name__ == '__main__':
    for dom_ in [
        "od.quest.ua", "kharkiv.en.cx", "quest.ua",
        "game.qeng.org",
        "https://game.odessaquest.com.ua/index.php",
        # "play.probeg.net.ua"
        # "pornhub.com",
    ]:
        dom_inst_ = Domain.from_url(dom_)
        print(dom_inst_, str(dom_inst_))
        # games_ = dom_inst_.get_games()
        # print(games_)
