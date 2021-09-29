"""
Bot-related constants
"""

import enum
import typing
import textwrap

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters

from meta import Language, EncounterGame
from constants import USER_LANGUAGE_KEY, DB_LOCATION, GAME_JOINER, \
    MAX_MESSAGE_LENGTH_TELEGRAM
from db_api import EncounterNewsDB
from translations import MENU_LOCALIZATION, MenuItem

__all__ = [
    "State", "MenuItem",
    "MENU_LOCALIZATION",
    "localize", "localize_dedent",
    "handle_choice",
    "kb_from_menu_items",
    "h", "games_desc_adaptive",
    "find_user_lang",
]


class State(enum.IntEnum):
    SettingsChoice = enum.auto()
    SettingsSet = enum.auto()
    SetLanguage = enum.auto()
    SetLanguageGetLang = enum.auto()
    InMainMenu = enum.auto()
    RuleTypeChoice = enum.auto()

    AddDomainRule = enum.auto()
    AddGameRuleGameIDPompt = enum.auto()
    AddGranularRuleDomainPrompt = enum.auto()
    WaitRuleToDelete = enum.auto()

    WaitDomainNameForGameID = enum.auto()
    WaitDomainNameForTeamID = enum.auto()
    WaitDomainNameForUserID = enum.auto()
    WaitDomainNameForAuthorID = enum.auto()
    WaitGameIDForGameID = enum.auto()
    WaitTeamIDForTeamID = enum.auto()
    WaitUserIDForUserID = enum.auto()
    WaitAuthorIDForAuthorID = enum.auto()
    ChooseDomainNameForGameID = enum.auto()
    ChooseDomainNameForTeamID = enum.auto()
    ChooseDomainNameForUserID = enum.auto()
    ChooseDomainNameForAuthorID = enum.auto()


def find_user_lang(update: Update, context: CallbackContext) -> Language:
    chat_id = update.message.chat_id
    if USER_LANGUAGE_KEY in context.chat_data:
        lang = context.chat_data[USER_LANGUAGE_KEY]
        lang = Language(lang)
    else:
        with EncounterNewsDB(DB_LOCATION) as db:
            lang = db.get_user_language(chat_id)
        context.chat_data[USER_LANGUAGE_KEY] = lang.value
    return lang


def localize(item: MenuItem, update: Update, context: CallbackContext) -> str:
    lang = find_user_lang(update, context)
    txt = MENU_LOCALIZATION[item][lang]
    return txt


def localize_dedent(item: MenuItem, update: Update, context: CallbackContext):
    msg = localize(item, update, context)
    msg = textwrap.dedent(msg).replace("\n", "")
    return msg


MENU_ITEM_TO_HANDLER = {
    MenuItem.AddRule: "add_rule_promt",
    MenuItem.DeleteRule: "delete_rule",
    MenuItem.ListRules: "list_rules",
    MenuItem.DomainRule: "add_domain_rule",
    MenuItem.GameRule: "add_game_rule",
    MenuItem.TeamRule: "add_team_rule",
    MenuItem.PlayerRule: "add_player_rule",
    MenuItem.AuthorRule: "add_author_rule",
    MenuItem.MenuNoAction: "settings_end",
    MenuItem.ListSubscribedGames: "get_subscribed_games",
}


CHOICES = {
    val: t
    for t, locs in MENU_LOCALIZATION.items()
    for lang, val in locs.items()
    if isinstance(val, str)
}


def handle_choice(update: Update, context: CallbackContext) -> typing.Optional[str]:
    choice = update.message.text
    if choice in CHOICES:
        mi = CHOICES[choice]
        handler = MENU_ITEM_TO_HANDLER[mi]
        return handler
    else:
        msg = localize(MenuItem.MenuChoiceIncorrect, update, context)
        update.message.reply_text(msg)
        return None


def kb_from_menu_items(
        menu_items: typing.List[MenuItem],
        update: Update, context: CallbackContext,
) -> typing.List[typing.List[str]]:
    reply_keyboard = [
        [localize(mi, update, context)]
        for mi in menu_items
    ]
    return reply_keyboard


def h(
        func: typing.Callable[[Update, CallbackContext], int],
        cancel_func: typing.Callable[[Update, CallbackContext], int],
) -> typing.List[
    typing.Union[MessageHandler, CommandHandler]
]:
    res = [
            MessageHandler(Filters.text & ~Filters.command, callback=func),
            CommandHandler("cancel", callback=cancel_func)
    ]
    return res


def split_game_desc(game: EncounterGame, language: Language):
    desc = game.to_str(language)
    pts = []
    for x in range(0, len(desc), MAX_MESSAGE_LENGTH_TELEGRAM):
        pt = desc[x:x + MAX_MESSAGE_LENGTH_TELEGRAM]
        pts.append(pt)
    return pts


def games_desc_adaptive(
        games: typing.List[EncounterGame],
        language: Language,
) -> typing.List[str]:
    games_chunks = []
    games_current_chunk = []
    for game in games:
        pt = game.to_str(language)
        games_current_chunk.append(pt)
        games_current_chunk_str = GAME_JOINER.join(games_current_chunk)
        total_length = len(games_current_chunk_str)
        if total_length >= MAX_MESSAGE_LENGTH_TELEGRAM:
            games_current_chunk.pop()
            if len(games_current_chunk) == 0:
                games_chunks.extend(split_game_desc(game, language))
            else:
                games_chunks.append(GAME_JOINER.join(games_current_chunk))
            games_current_chunk = []

    if games_current_chunk:
        games_chunks.append(GAME_JOINER.join(games_current_chunk))
    return games_chunks
