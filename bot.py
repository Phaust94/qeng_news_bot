
import enum
import typing

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
# from emoji import emojize

import os
import sys
cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from secrets import API_KEY
from version import __version__
from db_api import EncounterNewsDB
from constants import DB_LOCATION, MAX_MESSAGE_LENGTH_TELEGRAM, GAME_JOINER
from meta import EncounterGame, Language


class States(enum.IntEnum):
    SettingsChoice = enum.auto()
    AddDomain = enum.auto()
    AddDomainGetDomainName = enum.auto()
    AddDomainGetLanguage = enum.auto()
    GetDomainGames = enum.auto()
    GetDomainGamesGetDomainName = enum.auto()
    # GetDomainGamesGetLanguage = enum.auto()
    SettingsSet = enum.auto()


SETTINGS_LIST = {
    States.AddDomain: "Add domain to watched list",
    States.GetDomainGames: "Get current domain games",
    States.SettingsSet: "I'm done setting settings",
}
SETTINGS_LIST_INVERTED = {v: k for k, v in SETTINGS_LIST.items()}


# noinspection PyUnusedLocal
def settings_start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [
        [v]
        for _, v in sorted(SETTINGS_LIST.items(), key=lambda x: x[0])
    ]

    update.message.reply_text(
        "Let's set up some settings, shall we?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
        )
    )

    return States.SettingsChoice


# noinspection PyUnusedLocal
def settings(update: Update, context: CallbackContext) -> int:
    st = SETTINGS_LIST_INVERTED[update.message.text]
    cb = STATE_TO_HANDLERS[st]
    new_st = cb[0].callback(update, context)
    return new_st


# noinspection PyUnusedLocal
def settings_end(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Settings set')
    return ConversationHandler.END


# noinspection PyUnusedLocal
def add_domain(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Tell me domain URL you wish to follow")
    return States.AddDomainGetDomainName


# noinspection PyUnusedLocal
def add_domain_get_domain(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    domain = update.message.text
    context.user_data["domain"] = domain

    prompt = "Choose domain language"
    reply_keyboard = [
        [
            el.flag
            for el in Language
            if el.flag
        ]
    ]

    update.message.reply_text(
        prompt,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True
        )
    )

    return States.AddDomainGetLanguage


def add_domain_get_language(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    language = update.message.text
    language = Language.from_flag(language)
    domain = context.user_data["domain"]

    with EncounterNewsDB(DB_LOCATION) as db:
        res = db.add_domain_to_user_outer(chat_id, domain)

    update.message.reply_text(res)
    return States.SettingsChoice


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
        return States.SettingsChoice

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
    return States.GetDomainGamesGetDomainName


def split_game_desc(game: EncounterGame):
    desc = str(game)
    pts = []
    for x in range(0, len(desc), MAX_MESSAGE_LENGTH_TELEGRAM):
        pt = info[x:x + MAX_MESSAGE_LENGTH_TELEGRAM]
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
    settings_start(update, context)
    return States.SettingsChoice


# noinspection PyUnusedLocal
def error_handler(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"An error occurred: {{{context.error.__class__}}} {context.error}")
    return None


# noinspection PyUnusedLocal
def info(update: Update, context: CallbackContext) -> None:
    msg = f"This is an Encounter news bot\nVersion {__version__}"
    update.message.reply_text(msg)
    return None


STATE_TO_HANDLERS = {
    States.SettingsChoice: [
        MessageHandler(Filters.text & ~Filters.command, callback=settings),
        CommandHandler("settings", settings_start),
    ],
    States.AddDomain: [
        MessageHandler(Filters.text & ~Filters.command, add_domain),
        CommandHandler("settings", settings_start),
    ],
    States.AddDomainGetDomainName: [
        MessageHandler(Filters.text & ~Filters.command, add_domain_get_domain),
        CommandHandler("settings", settings_start),
    ],
    States.AddDomainGetLanguage: [
        MessageHandler(Filters.text & ~Filters.command, add_domain_get_language),
        CommandHandler("settings", settings_start),
    ],
    States.GetDomainGames: [
        MessageHandler(Filters.text & ~Filters.command, get_games),
        CommandHandler("settings", settings_start),
    ],
    States.GetDomainGamesGetDomainName: [
        MessageHandler(Filters.text & ~Filters.command, get_games_end),
        CommandHandler("settings", settings_start),
    ]
}


def main():
    updater = Updater(API_KEY, workers=4)

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('settings', settings_start),
            CommandHandler('start', settings_start)
        ],

        states=STATE_TO_HANDLERS,

        fallbacks=[MessageHandler(Filters.text, settings_end)]
    )

    updater.dispatcher.add_handler(conv_handler)

    updater.dispatcher.add_handler(CommandHandler("info", info))

    updater.dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    # q = updater.job_queue

    updater.idle()
    return None


if __name__ == '__main__':
    main()
