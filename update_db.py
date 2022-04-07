"""
DB Updater process
"""
import datetime
import os
import sys
import time
import re

import typing
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from telegram.ext import Updater
from telegram import Bot

from db_api import QEngNewsDB
from secrets import API_KEY, SEND_ONLY_TO_ADMIN
from meta_constants import DB_LOCATION, ADMIN_ID
from entities import Update
from entities.domain_meta import UpperLevelDomain

CHROME_DRIVER_PATH = os.path.join(__file__, "..", "data", "chromedriver.exe")

SEND_UPDATES = True
UPDATE_BLOCKLIST = {
    (UpperLevelDomain.QENG, 80),
    (UpperLevelDomain.QENG, 3115),
    (UpperLevelDomain.QENG, 3493),
    (UpperLevelDomain.QENG, 1279),
    (UpperLevelDomain.QENG, 431),             # Training games QENG
}


def is_blocked(update: Update) -> bool:
    for dom, gid in UPDATE_BLOCKLIST:

        if update.change.id != gid:
            continue

        if isinstance(dom, str) and re.findall(dom, update.change.domain.pretty_name):
            return True

        if isinstance(dom, UpperLevelDomain) and update.change.domain.upper_level_domain is dom:
            return True

    return False


def get_driver(executable_path: str):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=chrome_options, executable_path=executable_path)
    return driver


def send_update(upd: Update, bot: Bot, driver: typing.Optional[webdriver.Chrome]) -> typing.Optional[Update]:
    if is_blocked(upd):
        return None
    if not SEND_UPDATES:
        return None
    if SEND_ONLY_TO_ADMIN:
        upd.user_id = ADMIN_ID

    upd.sent_ts = datetime.datetime.utcnow()
    # noinspection PyBroadException
    try:
        bot.send_message(
            upd.user_id, upd.msg, parse_mode="HTML",
        )
        if upd.has_diffpic:
            with upd.diffpic(driver) as dp:
                # noinspection PyBroadException
                try:
                    bot.send_photo(upd.user_id, dp)
                except Exception:
                    with open(dp.name, "rb") as pic:
                        bot.send_document(upd.user_id, pic)

        upd.is_delivered = True
    except Exception as e:
        print("ERROR", upd, e, sep="\n")
        upd.is_delivered = False

    return upd


def update_db() -> None:
    updater = Updater(API_KEY, workers=1)
    bot = updater.bot
    with QEngNewsDB(DB_LOCATION) as db:
        updates = db.get_updates()

        driver = None
        if any(upd.has_diffpic for upd in updates):
            driver = get_driver(CHROME_DRIVER_PATH)

        for upd in updates:
            upd_sent = send_update(upd, bot, driver)
            if upd_sent is not None:
                time.sleep(2 / 30)

        db.updates_to_db(updates)
        db.commit_update()
        if driver is not None:
            driver.quit()

    succ_deliveries = [u for u in updates if u.is_delivered]
    unsucc_deliveries = [u for u in updates if not u.is_delivered]
    print(f"{len(succ_deliveries)} message(s) sent, {len(unsucc_deliveries)} failed deliveries")

    return None


if __name__ == '__main__':
    update_db()
