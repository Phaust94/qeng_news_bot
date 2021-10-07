"""
Custom classes constants
"""

from fake_useragent import UserAgent

__all__ = [
    "USER_AGENTS_FACTORY",
]

CHROME_DEFAULT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'"
USER_AGENTS_FACTORY = UserAgent(fallback=CHROME_DEFAULT)
