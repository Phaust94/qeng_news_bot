"""
DB Updater process
"""
import datetime
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

SEND_UPDATES = True
UPDATE_BLOCKLIST = {
    ('kharkiv.en.cx', 71875),       # Fucking "Реальная Виртуальность" spams updates as hell
    # ('kharkiv.en.cx', 72946),
}


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
            if (upd.change.domain.pretty_name, upd.change.id) in UPDATE_BLOCKLIST:
                continue
            if not SEND_UPDATES:
                continue

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
