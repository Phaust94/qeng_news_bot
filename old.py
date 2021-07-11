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


def split_game_desc(game: EncounterGame):
    desc = str(game)
    pts = []
    for x in range(0, len(desc), MAX_MESSAGE_LENGTH_TELEGRAM):
        pt = desc[x:x + MAX_MESSAGE_LENGTH_TELEGRAM]
        pts.append(pt)
    return pts


def games_desc_adaptive(games: typing.List[EncounterGame]) -> typing.List[str]:
    games_chunks = []
    games_current_chunk = []
    for game in games:
        pt = str(game)
        games_current_chunk.append(pt)
        games_current_chunk_str = GAME_JOINER.join(games_current_chunk)
        total_length = len(games_current_chunk_str)
        if total_length >= MAX_MESSAGE_LENGTH_TELEGRAM:
            games_current_chunk.pop()
            if len(games_current_chunk) == 0:
                games_chunks.extend(split_game_desc(game))
            else:
                games_chunks.append(GAME_JOINER.join(games_current_chunk))
            games_current_chunk = []

    if games_current_chunk:
        games_chunks.append(GAME_JOINER.join(games_current_chunk))
    return games_chunks


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
