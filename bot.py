"""
Bot main code
"""

import textwrap
import os
import sys

import typing
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler

cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from secrets import API_KEY
from version import __version__
from db_api import EncounterNewsDB
from constants import DB_LOCATION, USER_LANGUAGE_KEY, MAIN_MENU_COMMAND, \
    GAME_RULE_DOMAIN_KEY, RULE_ID_LENGTH
from meta import Language
from bot_constants import State, MENU_LOCALIZATION, MenuItem, localize, handle_choice,\
    kb_from_menu_items, h, localize_dedent, find_user_lang


# noinspection PyUnusedLocal
def prompt_language(update: Update, context: CallbackContext) -> int:
    msg = "Hello! Which language do you want me to speak?"
    kb = [
        [v]
        for v in Language.full_name_dict().values()
    ]
    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(
            kb,
        )
    )
    return State.SetLanguageGetLang


def store_user_lang(update: Update, context: CallbackContext) -> int:

    lang = update.message.text
    lang = Language.from_full_name(lang)
    context.chat_data[USER_LANGUAGE_KEY] = lang.value
    with EncounterNewsDB(DB_LOCATION) as db:
        db.set_user_language(update.message.chat_id, lang)
    lang_set_msg = MENU_LOCALIZATION[MenuItem.LangSet][lang]
    lang_set_msg = lang_set_msg.format(lang.full_name)
    update.message.reply_text(lang_set_msg)
    welcome_msg = MENU_LOCALIZATION[MenuItem.Welcome][lang]
    welcome_msg = textwrap.dedent(welcome_msg).replace("\n", "")
    update.message.reply_text(welcome_msg)
    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def settings_prompt(update: Update, context: CallbackContext) -> int:

    kb = kb_from_menu_items([
        MenuItem.AddRule, MenuItem.DeleteRule, MenuItem.ListRules, MenuItem.MenuNoAction
    ], update, context)

    msg = localize(MenuItem.MainMenu, update, context)

    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(kb),
    )

    return State.SettingsChoice


# noinspection PyUnusedLocal
def settings_choice_done(update: Update, context: CallbackContext) -> int:
    res = handle_choice(update, context)
    if isinstance(res, str):
        return globals()[res](update, context)
    else:
        return State.SettingsChoice


def add_rule_promt(update: Update, context: CallbackContext) -> int:
    kb = kb_from_menu_items([
        MenuItem.DomainRule, MenuItem.TeamRule, MenuItem.PlayerRule, MenuItem.GameRule,
    ], update, context)

    msg = localize(MenuItem.RuleTypeChoiceMenu, update, context)

    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(kb),
    )

    return State.RuleTypeChoice


def rule_type_choice_done(update: Update, context: CallbackContext) -> int:
    res = handle_choice(update, context)
    if isinstance(res, str):
        return globals()[res](update, context)
    else:
        return State.RuleTypeChoice


def delete_rule(update: Update, context: CallbackContext) -> int:
    rules = _find_rules(update, context)
    if rules:
        kb = [
            [r]
            for r in rules
        ]
        msg = localize(MenuItem.ChooseRuleToDelete, update, context)
        update.message.reply_text(
            msg, reply_markup=ReplyKeyboardMarkup(kb),
        )
        return State.WaitRuleToDelete
    else:
        msg = localize(MenuItem.NoRules, update, context)
        update.message.reply_text(msg)
        return settings_prompt(update, context)


def _find_rules(update: Update, context: CallbackContext) -> typing.List[str]:
    chat_id = update.message.chat_id
    with EncounterNewsDB(DB_LOCATION) as db:
        rules = db.get_user_rules(chat_id)
    lang = find_user_lang(update, context)
    rules = [
        r.to_str(lang)
        for r in rules
    ]
    return rules


def list_rules(update: Update, context: CallbackContext) -> int:
    rules = _find_rules(update, context)
    msg = "\n".join(
        r
        for r in rules
    )
    if not rules:
        msg = localize(MenuItem.NoRules, update, context)
    update.message.reply_text(msg, disable_web_page_preview=True)
    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def settings_end(update: Update, context: CallbackContext) -> int:
    msg = localize(MenuItem.MenuEnd, update, context)
    update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# noinspection PyUnusedLocal
def add_domain_rule(update: Update, context: CallbackContext) -> int:
    msg = localize_dedent(MenuItem.DomainPrompt, update, context)
    update.message.reply_text(msg, disable_web_page_preview=True)
    return State.AddDomainRule


# noinspection PyUnusedLocal
def add_domain_get_domain(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    domain = update.message.text

    with EncounterNewsDB(DB_LOCATION) as db:
        # TODO: add domain validation logic
        res = db.add_domain_to_user_outer(chat_id, domain)

    msg = localize(MenuItem.RuleAdded, update, context)
    update.message.reply_text(msg)

    return settings_prompt(update, context)


def wait_rule_to_delete(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    rule_text = update.message.text
    _, rule_id_txt = rule_text.split("[")
    rule_id = rule_id_txt[:-1]
    # noinspection PyBroadException
    try:
        assert len(rule_id) == RULE_ID_LENGTH, "Malformed rule ID"
    except Exception:
        msg = localize(MenuItem.RuleIDInvalid, update, context)
        update.message.reply_text(msg)
        return settings_prompt(update, context)
    with EncounterNewsDB(DB_LOCATION) as db:
        # TODO: add domain validation logic
        rule = db.get_user_rule_by_id(chat_id, rule_id)
        user_lang = find_user_lang(update, context)

        if rule_text != rule.to_str(user_lang):
            msg = localize(MenuItem.RuleIDInvalid, update, context)
            update.message.reply_text(msg)
            return settings_prompt(update, context)

        db.delete_user_rule_by_id(chat_id, rule_id)
    msg = localize(MenuItem.RuleDeleted, update, context)
    msg = msg.format(rule.to_str(user_lang))
    update.message.reply_text(msg)
    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def add_game_rule(update: Update, context: CallbackContext) -> int:
    msg = localize(MenuItem.DomainChoicePrompt, update, context)
    chat_id = update.message.chat_id

    with EncounterNewsDB(DB_LOCATION) as db:
        domains = db.get_user_domains(chat_id)
    kb = [
        [d]
        for d in domains
    ]
    update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb))
    return State.AddGameRuleGameIDPrompt


def add_game_rule_get_domain(update: Update, context: CallbackContext) -> int:
    domain = update.message.text
    context.chat_data[GAME_RULE_DOMAIN_KEY] = domain
    msg = localize_dedent(MenuItem.GameIDPrompt, update, context)
    update.message.reply_text(msg, disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())
    return State.AddGameRuleFinalize


def add_game_rule_get_game_id(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id

    domain = context.chat_data.pop(GAME_RULE_DOMAIN_KEY)
    if domain is None:
        msg = localize(MenuItem.DomainEmptyError, update, context)
        update.message.reply_text(msg)
        return add_rule_promt(update, context)
    game_id = update.message.text
    # noinspection PyBroadException
    try:
        game_id = int(game_id)
    except Exception:
        msg = localize(MenuItem.GameIDInvalid, update, context)
        update.message.reply_text(msg)
        return add_rule_promt(update, context)

    with EncounterNewsDB(DB_LOCATION) as db:
        db.add_mixed_rule_outer(chat_id, domain, game_id=game_id)

    msg = localize(MenuItem.RuleAdded, update, context)
    update.message.reply_text(msg)

    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def error_handler(update: Update, context: CallbackContext) -> None:
    errmsg = f"Error in chat {update.message.chat_id}: {{{context.error.__class__}}} {context.error}"
    print(errmsg)
    msg = localize(MenuItem.Error, update, context)
    update.message.reply_text(f"{msg} {{{context.error.__class__}}} {context.error}")
    return None


# noinspection PyUnusedLocal
def info(update: Update, context: CallbackContext) -> None:
    msg = localize(MenuItem.Info, update, context)
    msg = f"{msg} {__version__}"
    update.message.reply_text(msg)
    return None


STATE_TO_HANDLERS = {
    State.SetLanguage: h(prompt_language),
    State.SetLanguageGetLang: h(store_user_lang),
    State.InMainMenu: h(settings_prompt),
    State.SettingsChoice: h(settings_choice_done),
    State.RuleTypeChoice: h(rule_type_choice_done),
    State.AddDomainRule: h(add_domain_get_domain),
    State.AddGameRuleGameIDPrompt: h(add_game_rule_get_domain),
    State.AddGameRuleFinalize: h(add_game_rule_get_game_id),
    State.WaitRuleToDelete: h(wait_rule_to_delete),

    # State.AddDomain: h(add_domain_rule),
}


def main():
    updater = Updater(API_KEY, workers=4)

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(MAIN_MENU_COMMAND, settings_prompt),
            CommandHandler('start', prompt_language)
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
