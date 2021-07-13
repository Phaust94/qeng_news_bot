"""
Bot-related constants
"""

import enum
import typing
import textwrap

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters


from meta import Language
from constants import USER_LANGUAGE_KEY, DB_LOCATION
from db_api import EncounterNewsDB

__all__ = [
    "State", "MenuItem",
    "MENU_LOCALIZATION",
    "localize", "localize_dedent",
    "handle_choice",
    "kb_from_menu_items",
    "h",
]


class State(enum.IntEnum):
    SettingsChoice = enum.auto()
    # GetDomainGames = enum.auto()
    # GetDomainGamesGetDomainName = enum.auto()
    # GetDomainGamesGetLanguage = enum.auto()
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
    WaitGameIDForGameID = enum.auto()
    WaitTeamIDForTeamID = enum.auto()
    WaitUserIDForUserID = enum.auto()
    ChooseDomainNameForGameID = enum.auto()
    ChooseDomainNameForTeamID = enum.auto()
    ChooseDomainNameForUserID = enum.auto()


class MenuItem(enum.Enum):
    LangSet = enum.auto()
    MainMenu = enum.auto()
    Error = enum.auto()
    Info = enum.auto()
    AddRule = enum.auto()
    DeleteRule = enum.auto()
    ListRules = enum.auto()
    MenuNoAction = enum.auto()
    MenuChoiceIncorrect = enum.auto()
    Welcome = enum.auto()
    MenuEnd = enum.auto()
    DomainRule = enum.auto()
    GameRule = enum.auto()
    PlayerRule = enum.auto()
    TeamRule = enum.auto()
    RuleTypeChoiceMenu = enum.auto()
    DomainPrompt = enum.auto()
    RuleAdded = enum.auto()
    DomainChoicePrompt = enum.auto()
    GameIDPrompt = enum.auto()
    DomainEmptyError = enum.auto()
    IDInvalid = enum.auto()
    NoRules = enum.auto()
    ChooseRuleToDelete = enum.auto()
    RuleIDInvalid = enum.auto()
    RuleDeleted = enum.auto()
    AnotherDomain = enum.auto()
    RoughRuleDescription = enum.auto()
    GranularRuleDescription = enum.auto()
    DomainInvalid = enum.auto()
    TeamIDPrompt = enum.auto()
    PlayerIDPrompt = enum.auto()


MENU_LOCALIZATION = {
    MenuItem.LangSet: {
        Language.Russian: "Язык успешно установлен: {}",
        Language.English: "Language successfully set: {}",
    },
    MenuItem.MainMenu: {
        Language.Russian: "Что бы вы хотели сделать?",
        Language.English: "Would you like to do?"
    },
    MenuItem.Error: {
        Language.Russian: "Произошла ошибка:",
        Language.English: "An error occurred:",
    },
    MenuItem.Info: {
        Language.Russian: "Это новостной бот Энки\nВерсия",
        Language.English: "This is an Encounter news bot\nVersion",
    },
    MenuItem.Welcome: {
        Language.Russian: """
        Приветствую! Я - бот, который поможет вам всегда быть в курсе 
        всех новостей Энки. Я могу следить за всеми играми на определённом домене, за какой-то конкретной игрой 
        или за всеми играми вашей команды (или вас) (на одиночных играх).
        Когда на сайте будут какие-то изменения в анонсе игры, или появятся новые игры - 
        я обязательно вам об этом сообщу. Сейчас рекомендую добавить ваше первое правило отслеживания домена.""",
        Language.English: """
        Hello! I am a bot who will help you always be up-to-date 
        with all Encounter games. I can track all games in a given domain, track a certain game, or
         track all games where your team (or you) participates. When there are any changes to a game announcement,
         or there's a new game going on - I'll semd you a message. Now I suggest you add your first domain 
         tracking rule.""",
    },
    MenuItem.AddRule: {
        Language.Russian: "Добавить правило слежения",
        Language.English: "Add tracking rule",
    },
    MenuItem.DeleteRule: {
        Language.Russian: "Удалить правило слежения",
        Language.English: "Delete tracking rule",
    },
    MenuItem.ListRules: {
        Language.Russian: "Показать список правил слежения",
        Language.English: "List tracking rules",
    },
    MenuItem.MenuChoiceIncorrect: {
        Language.Russian: "Неправильный выбор! Попробуйте ещё раз.",
        Language.English: "Incorrect choice. Try again.",
    },
    MenuItem.MenuEnd: {
        Language.Russian: "Выбор настроек окончен. Если хотите совершить настройку ещё раз - вызовите комманду /menu",
        Language.English: "Done changing settings. If you wish to chanage settings oce again - just call /menu",
    },
    MenuItem.DomainRule: {
        Language.Russian: "Слежение за доменом",
        Language.English: "Whole domain tracking",
    },
    MenuItem.GameRule: {
        Language.Russian: "Слежение за отдельной игрой в домене",
        Language.English: "Single game tracking (within one domain)",
    },
    MenuItem.TeamRule: {
        Language.Russian: "Слежение за играми команды в домене",
        Language.English: "Single team games tracking (within one domain)",
    },
    MenuItem.PlayerRule: {
        Language.Russian: "Слежение за играми конкретного игрока в домене (для одиночных игр)",
        Language.English: "Specific player games tracking (within one domain) (for single games)",
    },
    MenuItem.RuleTypeChoiceMenu: {
        Language.Russian: "Выберите тип правила слежения",
        Language.English: "Choose tracking rule type",
    },
    MenuItem.DomainPrompt: {
        Language.Russian: """
        Пришлите мне ссылку на домен. Например, http://kharkiv.en.cx/.
         Если в домене разный список игр для разных языков - то пришлите ссылку с указанием языка домена. 
        Например, http://kharkiv.en.cx/?lang=ru""",
        Language.English: """
        Send domain URL. E.g. http://kharkiv.en.cx/.
         If a domain has different games list for different languages - then specify 
        the language you wish to track in the link. E.g. http://kharkiv.en.cx/?lang=ru""",
    },
    MenuItem.RoughRuleDescription: {
        Language.Russian: """
        Я буду присылать вам только важные новости: перенос игры или большое изменение в описании. 
        Мелкие изменения я отслеживаю только в командных / индивидуальных / игровых правилах.""",
        Language.English: """
        I will send you only important updates: when game dates changed or if
         there is a major change in a game description. Minor changes are only tracked
         under team / individual / game rules.""",
    },

    MenuItem.RuleAdded: {
        Language.Russian: "Правило\n{}\nдобавлено успешно",
        Language.English: "Rule\n{}\nadded successfully",
    },
    MenuItem.DomainChoicePrompt: {
        Language.Russian: "Выберите домен",
        Language.English: "Choose domain",
    },
    MenuItem.GameIDPrompt: {
        Language.Russian: """
        Пришлите ID игры, которую вы хотите отслеживать. 
         Например, для игры http://kharkiv.en.cx/GameDetails.aspx?gid=72405 ID будет 72405""",
        Language.English: """
        Send game ID you wish to track. 
         E.g. for game http://kharkiv.en.cx/GameDetails.aspx?gid=72405, ID is 72405""",
    },
    MenuItem.DomainEmptyError: {
        Language.Russian: "Не могу определить название домена. Попробуйте сначала.",
        Language.English: "Can't get domain name. Please, try again.",
    },
    MenuItem.IDInvalid: {
        Language.Russian: "ID неправильный. Попробуйте сначала.",
        Language.English: "ID is invalid. Please, try again.",
    },
    MenuItem.NoRules: {
        Language.Russian: "У вас пока нет правил",
        Language.English: "You don't have any rules just yet",
    },
    MenuItem.MenuNoAction: {
        Language.Russian: "Ничего",
        Language.English: "Nothing",
    },
    MenuItem.ChooseRuleToDelete: {
        Language.Russian: "Выберите правило, которое хотите удалить",
        Language.English: "Choose rule you want to delete",
    },
    MenuItem.RuleIDInvalid: {
        Language.Russian: "ID правила неверный. Попробуйте сначала.",
        Language.English: "Rule ID invalid. Please, try again.",
    },
    MenuItem.RuleDeleted: {
        Language.Russian: "Правило\n{}\nудалено успешно.",
        Language.English: "Rule\n{}\ndeleted successfully.",
    },
    MenuItem.AnotherDomain: {
        Language.Russian: "Другой домен",
        Language.English: "Another domain",
    },
    MenuItem.GranularRuleDescription: {
        Language.Russian: """
        Я буду присылать вам все новости: перенос игры, любое изменение в описании игры, новое сообщение на форуме.
         Также с этим правилом вы можете следить за играми без остлеживания всего домена целиком.""",
        Language.English: """
        I will send you all updates: when game dates changed, if there's any change in a game description,
        or when there's a new forum post.
         With this rule you can also track games without tracking the whole domain.""",
    },
    MenuItem.DomainInvalid: {
        Language.Russian: "Некооректный домен. Попробуйте ещё раз.",
        Language.English: "Invalid domain. Try again.",
    },
    MenuItem.TeamIDPrompt: {
        Language.Russian: """
    Пришлите ID команды, игры которой вы хотите отслеживать. 
     Например, для команды http://kharkiv.en.cx/Teams/TeamDetails.aspx?tid=183339 ID будет 183339""",
        Language.English: """
    Send team ID you wish to follow. 
     E.g. for team http://kharkiv.en.cx/Teams/TeamDetails.aspx?tid=183339, ID is 183339""",
    },
    MenuItem.PlayerIDPrompt: {
        Language.Russian: """
    Пришлите ID игрока, игры которого вы хотите отслеживать (для одиночных игр).  
     Например, для игрока http://kharkiv.en.cx/UserDetails.aspx?uid=1724452 ID будет 1724452""",
        Language.English: """
    Send player ID you wish to follow (for single games). 
     E.g. for player http://kharkiv.en.cx/UserDetails.aspx?uid=1724452, ID is 1724452""",
    },
}


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
    MenuItem.MenuNoAction: "settings_end",
}


CHOICES = {
    val: t
    for t, locs in MENU_LOCALIZATION.items()
    for lang, val in locs.items()
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
