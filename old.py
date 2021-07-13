"""
Bot main code
"""

import textwrap
import typing
import os
import sys

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler

cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from secrets import API_KEY
from version import __version__
from db_api import EncounterNewsDB
from constants import DB_LOCATION, MAX_MESSAGE_LENGTH_TELEGRAM, GAME_JOINER, USER_LANGUAGE_KEY, MAIN_MENU_COMMAND
from meta import EncounterGame, Language
from bot_constants import State, MENU_LOCALIZATION, MenuItem, localize, handle_choice, kb_from_menu_items, h


# noinspection PyUnusedLocal
def get_games(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    with EncounterNewsDB(DB_LOCATION) as db:
        domains = db.get_user_domains(chat_id)
    reply_keyboard = [
        [d]
        for d in domains
    ]
    if not domains:
        update.message.reply_text("You don't have any domains to get")
        return State.SettingsChoice

    if len(domains) == 1:
        update.message.text = domains[0]
        res = get_games_end(update, context)
        return res

    reply_keyboard.append(["All"])

    update.message.reply_text(
        "Which domain do you want to see the games for?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True
        )
    )
    return State.GetDomainGamesGetDomainName


# noinspection PyUnusedLocal
def get_games_end(update: Update, context: CallbackContext) -> int:
    domain = update.message.text
    chat_id = update.message.chat_id

    with EncounterNewsDB(DB_LOCATION) as db:
        games = db.show_games_outer(chat_id, domain)

    msgs = games_desc_adaptive(games)
    for msg in msgs:
        update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)

    return settings_promt(update, context)


STATE_TO_HANDLERS = {
    State.GetDomainGames: h(get_games),
    State.GetDomainGamesGetDomainName: h(get_games_end),
}
