import os

__all__ = [
    "DB_LOCATION",
    "UPDATE_FREQUENCY_SECONDS",
]

DB_LOCATION = os.path.join(__file__, "..", "data", "bot_db.sqlite")
UPDATE_FREQUENCY_SECONDS = 6 * 60 * 60
