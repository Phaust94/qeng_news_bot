"""
DB Updater process
"""

import os
import sys

import pandas as pd

cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from telegram.ext import Updater

from db_api import EncounterNewsDB
from constants import DB_LOCATION, UPDATE_FREQUENCY_SECONDS
from meta import Change, Language
from secrets import API_KEY


# TODO: GAME COMING UP SOON CHANGE TYPE
# TODO: past games track comments (through new rule type)

def main() -> None:
    updater = Updater(API_KEY, workers=1)
    with EncounterNewsDB(DB_LOCATION) as db:
        domains_due = db.find_domains_due(UPDATE_FREQUENCY_SECONDS)
        if domains_due:
            db.update_domains(domains_due)
            users_to_notify = db.users_to_notify()
        else:
            users_to_notify = pd.DataFrame()

    for _, row in users_to_notify.iterrows():
        tg_id = row["USER_ID"]
        # noinspection PyTypeChecker
        change = Change.from_json(row.to_dict())
        lang = Language(row["LANGUAGE"])
        msg = change.to_str(lang)
        updater.bot.send_message(
            tg_id, msg, parse_mode="HTML",
        )

    return None


if __name__ == '__main__':
    main()
