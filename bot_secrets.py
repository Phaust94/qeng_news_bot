import os

API_KEY = os.environ["API_KEY"]
SEND_ONLY_TO_ADMIN = os.environ.get("SEND_ONLY_TO_ADMIN", 'false') == 'true'