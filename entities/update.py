
from __future__ import annotations

import datetime
from dataclasses import dataclass
import typing
import os
import time
from io import BytesIO
import tempfile
from contextlib import contextmanager

import pandas as pd
from selenium import webdriver
from PIL import Image

from translations import Language, MenuItem, MENU_LOCALIZATION
from description_diff import html_diffs
from entities.change import Change, ChangeType

__all__ = [
    "Update",
]


@dataclass
class Update:
    user_id: int
    language: Language
    change: Change
    sent_ts: datetime.datetime = None
    is_delivered: bool = False

    @staticmethod
    def test_fullpage_screenshot(
            file: str,
            path: str,
            driver: webdriver.Chrome
    ) -> None:
        driver.get(file)
        time.sleep(0.25)
        element = driver.find_element_by_id('main')  # find part of the page you want image of

        driver.set_window_size(800, 100)
        time.sleep(0.25)
        total_height = element.size["height"] + 200
        driver.set_window_size(800, total_height)
        time.sleep(0.25)

        location = element.location
        size = element.size

        png = driver.get_screenshot_as_png()  # saves screenshot of entire page

        im = Image.open(BytesIO(png))  # uses PIL library to open image in memory

        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

        im = im.crop((left, top, right, bottom))  # defines crop points
        im.save(path)  # saves new cropped image
        return None

    @classmethod
    def create_diff(
            cls,
            old_description: str, new_description: str, lang: Language,
            driver: webdriver.Chrome,
    ) -> typing.Tuple[typing.Any, str]:
        names = MENU_LOCALIZATION[MenuItem.DescriptionBeforeAfter][lang]
        res = html_diffs(old_description, new_description, *names)
        html_fd, html_path = tempfile.mkstemp(suffix=".html")
        pic_fd, pic_path = tempfile.mkstemp(suffix=".png")
        with open(html_path, 'w', encoding='utf-8') as tmp:
            tmp.write(res)
        try:
            cls.test_fullpage_screenshot(f"file://{html_path}", pic_path, driver)
        finally:
            os.close(html_fd)
            os.remove(html_path)
        return pic_fd, pic_path

    @property
    def msg(self) -> str:
        msg_ = self.change.to_str(self.language)
        return msg_

    @property
    def has_diffpic(self) -> bool:
        return ChangeType.DescriptionChanged in self.change.current_changes

    @contextmanager
    def diffpic(self, driver: webdriver.Chrome):
        pic_fd, pic_path = self.create_diff(
            self.change.old_description_truncated or "",
            self.change.new_description_truncated or "",
            lang=self.language,
            driver=driver,
        )
        try:
            with open(pic_path, "rb") as pic:
                yield pic
        finally:
            os.close(pic_fd)
            os.remove(pic_path)
        return None

    @classmethod
    def from_row(
            cls,
            row: pd.Series,
    ) -> Update:
        user_id = row["USER_ID"]
        lang = Language(row["LANGUAGE"])
        # noinspection PyTypeChecker
        change = Change.from_json(row.to_dict())
        inst = cls(
            user_id, lang, change
        )
        return inst

    def to_json(self) -> typing.Dict[str, typing.Any]:
        res = {
            "USER_ID": self.user_id,
            **self.change.to_json(),
            "DELIVERED": self.sent_ts,
            "IS_DELIVERED": int(self.is_delivered),
        }
        return res
