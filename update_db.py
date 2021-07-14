"""
DB Updater process
"""

import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from telegram.ext import Updater

from db_api import EncounterNewsDB
from secrets import API_KEY
from constants import DB_LOCATION

CHROME_DRIVER_PATH = os.path.join(__file__, "..", "data", "chromedriver.exe")

DB_LOC = os.path.join(__file__, "..", "data", "bot_db - Copy (3).sqlite")


def get_driver(executable_path: str):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=chrome_options, executable_path=executable_path)
    return driver


def update_db() -> None:
    updater = Updater(API_KEY, workers=1)
    bot = updater.bot
    with EncounterNewsDB(DB_LOCATION) as db:
        updates = db.get_updates()

        driver = None
        if any(upd.has_diffpic for upd in updates):
            driver = get_driver(CHROME_DRIVER_PATH)

        for upd in updates:

            bot.send_message(
                upd.user_id, upd.msg, parse_mode="HTML",
            )
            if upd.has_diffpic:
                with upd.diffpic(driver) as dp:
                    bot.send_photo(upd.user_id, dp)

        db.commit_update()

    print(len(updates), "message(s) sent")

    return None


if __name__ == '__main__':
    update_db()
