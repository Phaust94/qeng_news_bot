"""
Status check updates
"""

import os
import sys

cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from telegram.ext import Updater

from db_api import QEngNewsDB
from secrets import API_KEY
from meta_constants import DB_LOCATION, ADMIN_ID
from bot_constants import MENU_LOCALIZATION, MenuItem
from translations import Language


def status_update() -> None:
    updater = Updater(API_KEY, workers=1)
    bot = updater.bot
    with QEngNewsDB(DB_LOCATION) as db:
        res = db.count_updates()
    msg = MENU_LOCALIZATION[MenuItem.BotStatusReportAllowed][Language.Ukrainian]
    msg = msg.format(*res)
    bot.send_message(ADMIN_ID, msg)

    return None


if __name__ == '__main__':
    status_update()
