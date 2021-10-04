"""
Bot main code
"""

import textwrap
import os
import sys
import functools

import typing
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler

import constants

cur_dir = os.path.dirname(__file__)
if cur_dir not in sys.path:
    sys.path.append(cur_dir)

from secrets import API_KEY
from version import __version__
from db_api import EncounterNewsDB
from constants import DB_LOCATION, USER_LANGUAGE_KEY, MAIN_MENU_COMMAND, \
    GAME_RULE_DOMAIN_KEY, RULE_ID_LENGTH, InvalidDomainError, DEFAULT_DAYS_IN_FUTURE
from meta import Language
from bot_constants import State, MENU_LOCALIZATION, MenuItem, localize, handle_choice,\
    kb_from_menu_items, localize_dedent, find_user_lang, games_desc_adaptive
from bot_constants import h as h_full


# noinspection PyUnusedLocal
def prompt_language(update: Update, context: CallbackContext) -> int:

    with EncounterNewsDB(DB_LOCATION) as db:
        db.start_user_updates(update.message.chat_id)

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
    update.message.reply_text(welcome_msg, parse_mode="HTML")
    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def settings_prompt(update: Update, context: CallbackContext) -> int:

    kb = kb_from_menu_items(
        [
            MenuItem.AddRule, MenuItem.DeleteRule, MenuItem.ListRules,
            MenuItem.ListSubscribedGames, MenuItem.MenuNoAction
        ],
        update,
        context
    )

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
    with EncounterNewsDB(DB_LOCATION) as db:
        is_ok_to_add = db.is_user_within_rule_limits(update.message.chat_id)
    if not is_ok_to_add:
        msg = localize_dedent(MenuItem.RuleLimitReached, update, context)
        update.message.reply_text(msg)
        return settings_prompt(update, context)

    kb = kb_from_menu_items([
        MenuItem.DomainRule, MenuItem.TeamRule, MenuItem.PlayerRule, MenuItem.GameRule,
        MenuItem.AuthorRule,
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
    rules = _find_rules(update, context, add_href=False, force_no_href=True)
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


def _find_rules(
    update: Update, context: CallbackContext,
    add_href: bool = False, force_no_href: bool = False,
) -> typing.List[str]:
    chat_id = update.message.chat_id
    with EncounterNewsDB(DB_LOCATION) as db:
        rules = db.get_user_rules(chat_id)
    lang = find_user_lang(update, context)
    rules = [
        r.to_str(lang, add_href=add_href, force_no_href=force_no_href)
        for r in rules
    ]
    return rules


def list_rules(update: Update, context: CallbackContext) -> int:
    rules = _find_rules(update, context, add_href=True, force_no_href=False)
    msg = "\n".join(
        r
        for r in rules
    )
    if not rules:
        msg = localize(MenuItem.NoRules, update, context)
    update.message.reply_text(msg, disable_web_page_preview=True, parse_mode="HTML")
    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def settings_end(update: Update, context: CallbackContext) -> int:
    msg = localize(MenuItem.MenuEnd, update, context)
    update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# noinspection PyUnusedLocal
def add_domain_rule(update: Update, context: CallbackContext) -> int:
    desc = localize_dedent(MenuItem.RoughRuleDescription, update, context)
    update.message.reply_text(desc, reply_markup=ReplyKeyboardRemove())
    msg = localize_dedent(MenuItem.DomainPrompt, update, context)
    update.message.reply_text(msg, disable_web_page_preview=True)
    return State.AddDomainRule


# noinspection PyUnusedLocal
def add_domain_get_domain(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    domain = update.message.text

    with EncounterNewsDB(DB_LOCATION) as db:
        # TODO: add domain validation logic
        try:
            succ, rule = db.add_domain_to_user_outer(chat_id, domain)
        except InvalidDomainError:
            msg = localize(MenuItem.DomainInvalid, update, context)
            update.message.reply_text(msg)
            return settings_prompt(update, context)

    item = MenuItem.RuleAdded if succ else MenuItem.RuleNotAdded
    msg = localize(item, update, context)
    lang = find_user_lang(update, context)
    msg = msg.format(rule.to_str(lang), disable_web_page_preview=True)
    update.message.reply_text(msg, parse_mode='HTML')

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

        if rule_text != rule.to_str(user_lang, add_href=False, force_no_href=True):
            msg = localize(MenuItem.RuleIDInvalid, update, context)
            update.message.reply_text(msg)
            return settings_prompt(update, context)

        db.delete_user_rule_by_id(chat_id, rule_id)
        db.prune_rule_descriptions()
        db.prune_domain_query_status()
    msg = localize(MenuItem.RuleDeleted, update, context)
    msg = msg.format(rule.to_str(user_lang), disable_web_page_preview=True)
    update.message.reply_text(msg, disable_web_page_preview=True, parse_mode='HTML')
    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def add_granular_rule(
        update: Update,
        context: CallbackContext,
        wait_domain_state: State,
) -> int:
    desc = localize_dedent(MenuItem.GranularRuleDescription, update, context)
    update.message.reply_text(desc)
    msg = localize(MenuItem.DomainChoicePrompt, update, context)
    chat_id = update.message.chat_id

    with EncounterNewsDB(DB_LOCATION) as db:
        domains = db.get_user_domains(chat_id)

    another_domain = localize(MenuItem.AnotherDomain, update, context)
    kb = [
        [d]
        for d in domains
    ] + [[another_domain]]
    update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb))
    return wait_domain_state


def add_granular_rule_get_domain(
        update: Update, context: CallbackContext,
        prompt: MenuItem, promt_state: State, wait_state: State,
) -> int:
    domain = update.message.text
    if domain == localize(MenuItem.AnotherDomain, update, context):
        msg = localize_dedent(MenuItem.DomainPrompt, update, context)
        update.message.reply_text(msg, disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())
        return wait_state
    else:
        return accept_domain_granular_rule(update, context, prompt, promt_state)


def accept_domain_granular_rule(
        update: Update, context: CallbackContext,
        prompt: MenuItem, state: State,
) -> int:
    domain = update.message.text

    with EncounterNewsDB(DB_LOCATION) as db:
        try:
            db.track_domain_outer(domain)
        except InvalidDomainError:
            msg = localize(MenuItem.DomainInvalid, update, context)
            update.message.reply_text(msg)
            return settings_prompt(update, context)

    context.chat_data[GAME_RULE_DOMAIN_KEY] = domain
    msg = localize_dedent(prompt, update, context)
    update.message.reply_text(msg, disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())
    return state


def add_granular_rule_get_id(
        update: Update,
        context: CallbackContext,
        key: str
) -> int:
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
        msg = localize(MenuItem.IDInvalid, update, context)
        update.message.reply_text(msg)
        return add_rule_promt(update, context)

    with EncounterNewsDB(DB_LOCATION) as db:
        kwargs = {key: game_id}
        succ, rule = db.add_mixed_rule_outer(chat_id, domain, **kwargs)

    item = MenuItem.RuleAdded if succ else MenuItem.RuleNotAdded
    msg = localize(item, update, context)
    lang = find_user_lang(update, context)
    msg = msg.format(rule.to_str(lang), disable_web_page_preview=True)
    update.message.reply_text(msg, parse_mode='HTML')

    return settings_prompt(update, context)


# noinspection PyUnusedLocal
def get_subscribed_games(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    msg = localize(MenuItem.GamesInFutureWarning, update, context)
    update.message.reply_text(msg)

    with EncounterNewsDB(DB_LOCATION) as db:
        games = db.get_all_user_games(chat_id, DEFAULT_DAYS_IN_FUTURE)

    lang = find_user_lang(update, context)
    msgs = games_desc_adaptive(games, lang)
    for msg in msgs:
        update.message.reply_text(
            msg,
            parse_mode="HTML", disable_web_page_preview=True,
        )

    if not msgs:
        msg = localize(MenuItem.NoSubscribedGames, update, context)
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
    with EncounterNewsDB(DB_LOCATION) as db:
        updates_on = db.get_updates_on_off(update.message.chat_id)

    st = "UpdatesOn" if updates_on else "UpdatesOff"
    it = getattr(MenuItem, st)
    status_txt = localize(it, update, context)
    msg = msg.format(
        __version__,
        status_txt,
    )
    update.message.reply_text(msg)
    return None


# noinspection PyUnusedLocal
def stop(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    with EncounterNewsDB(DB_LOCATION) as db:
        db.stop_user_updates(chat_id)
    msg = localize(MenuItem.BotStopped, update, context)
    update.message.reply_text(msg)
    return None


# noinspection PyUnusedLocal
def status_check(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id != constants.ADMIN_ID:
        msg = localize(MenuItem.BotStatusReportNotAllowed, update, context)
    else:
        with EncounterNewsDB(DB_LOCATION) as db:
            res = db.count_updates()
        msg = localize(MenuItem.BotStatusReportAllowed, update, context)
        msg = msg.format(*res)
    update.message.reply_text(msg)
    return None


# noinspection PyUnusedLocal
def help_(update: Update, context: CallbackContext) -> None:
    msg = localize(MenuItem.Help, update, context)
    update.message.reply_text(msg, parse_mode="HTML")
    return None


h = functools.partial(h_full, cancel_func=settings_prompt)

STATE_TO_HANDLERS = {
    State.SetLanguage: h(prompt_language),
    State.SetLanguageGetLang: h(store_user_lang),
    State.InMainMenu: h(settings_prompt),
    State.SettingsChoice: h(settings_choice_done),
    State.RuleTypeChoice: h(rule_type_choice_done),
    State.AddDomainRule: h(add_domain_get_domain),
    State.WaitRuleToDelete: h(wait_rule_to_delete),
}

GRANULAR_RULES = [
    (
        "game", MenuItem.GameIDPrompt,
        State.ChooseDomainNameForGameID, State.WaitDomainNameForGameID, State.WaitGameIDForGameID
    ),
    (
        "team", MenuItem.TeamIDPrompt,
        State.ChooseDomainNameForTeamID, State.WaitDomainNameForTeamID, State.WaitTeamIDForTeamID
    ),
    (
        "player", MenuItem.PlayerIDPrompt,
        State.ChooseDomainNameForUserID, State.WaitDomainNameForUserID, State.WaitUserIDForUserID
    ),
    (
        "author", MenuItem.AuthorIDPrompt,
        State.ChooseDomainNameForAuthorID, State.WaitDomainNameForAuthorID, State.WaitAuthorIDForAuthorID
    ),

]
for name, pr, cdn, wdn, wid in GRANULAR_RULES:
    func_name = f"add_{name}_rule"
    func = functools.partial(
        add_granular_rule,
        wait_domain_state=cdn,
    )
    globals()[func_name] = func

    accept_domain_pt = functools.partial(
        accept_domain_granular_rule,
        prompt=pr, state=wid
    )
    cdn_handler = functools.partial(
        add_granular_rule_get_domain,
        prompt=pr, promt_state=wid,
        wait_state=wdn,
    )
    get_id = functools.partial(add_granular_rule_get_id, key=f"{name}_id")
    STATE_TO_HANDLERS[cdn] = h(cdn_handler)
    STATE_TO_HANDLERS[wdn] = h(accept_domain_pt)
    STATE_TO_HANDLERS[wid] = h(get_id)


def main():
    updater = Updater(API_KEY, workers=4)

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(MAIN_MENU_COMMAND, settings_prompt),
            CommandHandler('start', prompt_language)
        ],

        states=STATE_TO_HANDLERS,

        fallbacks=[MessageHandler(Filters.text, settings_end)],
        per_chat=True,
        per_user=False,
    )

    updater.dispatcher.add_handler(conv_handler)

    updater.dispatcher.add_handler(CommandHandler("help", help_))

    updater.dispatcher.add_handler(CommandHandler("info", info))

    updater.dispatcher.add_handler(CommandHandler("stop", stop))

    updater.dispatcher.add_handler(CommandHandler("status", status_check))

    updater.dispatcher.add_error_handler(error_handler)

    updater.start_polling()

    updater.idle()
    return None


if __name__ == '__main__':
    main()
