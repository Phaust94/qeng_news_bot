"""
DB Updater process
"""

import os
import sys
cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from db_api import EncounterNewsDB
from constants import DB_LOCATION, UPDATE_FREQUENCY_SECONDS


def main() -> None:
    with EncounterNewsDB(DB_LOCATION) as db:
        domains_due = db.find_domains_due(UPDATE_FREQUENCY_SECONDS)
        db.update_domains(domains_due)

    return None


if __name__ == '__main__':
    main()
