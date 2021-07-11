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
    AddGameRuleFinalize = enum.auto()
    AddGameRuleGameIDPrompt = enum.auto()


class MenuItem(enum.Enum):
    LangSet = enum.auto()
    MainMenu = enum.auto()
    Error = enum.auto()
    Info = enum.auto()
    AddRule = enum.auto()
    DeleteRule = enum.auto()
    ListRules = enum.auto()
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
    GameIDInvalid = enum.auto()
    NoRules = enum.auto()


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
        Пришлите мне ссылку на домен, за которым вы хотите следить. Например, http://kharkiv.en.cx/.
         Если в домене разный список игр для разных языков - то пришлисте ссылку с указанием языка домена. 
        Например, http://kharkiv.en.cx/?lang=en""",
        Language.English: """
        Send domain URL you want me to track. E.g. http://kharkiv.en.cx/.
         If a domain has different games list for different languages - then specify 
        the language you wish to track in the link. E.g. http://kharkiv.en.cx/?lang=en"""
    },
    MenuItem.RuleAdded: {
        Language.Russian: "Правило успешно добавлено",
        Language.English: "Rule successfully added",
    },
    MenuItem.DomainChoicePrompt: {
        Language.Russian: "Выберите домен, в котором находится игра",
        Language.English: "Choose domain of the game",
    },
    MenuItem.GameIDPrompt: {
        Language.Russian: """
        Пришлите ID игры. 
         Например, для игры http://kharkiv.en.cx/GameDetails.aspx?gid=72405 ID будет 72405""",
        Language.English: """
        Send game ID. 
         E.g. for game http://kharkiv.en.cx/GameDetails.aspx?gid=72405, ID is 72405""",
    },
    MenuItem.DomainEmptyError: {
        Language.Russian: "Не могу определить название домена. Попробуйте сначала.",
        Language.English: "Can't get domain name. Please, try again.",
    },
    MenuItem.GameIDInvalid: {
        Language.Russian: "ID игры неправильный. Попробуйте сначала.",
        Language.English: "Game ID invalid. Please, try again.",
    },
    MenuItem.NoRules: {
        Language.Russian: "У вас пока нет правил",
        Language.English: "You don't have any rules just yet",
    }
}


def find_user_lang(update: Update, context: CallbackContext) -> Language:
    chat_id = update.message.chat_id
    if USER_LANGUAGE_KEY in context.chat_data:
        lang = context.chat_data[USER_LANGUAGE_KEY]
        lang = Language(lang)
    else:
        with EncounterNewsDB(DB_LOCATION) as db:
            lang = db.get_user_language(chat_id)
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
    MenuItem.TeamRule: None,  # TODO
    MenuItem.PlayerRule: None,  # TODO
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


def h(func: typing.Callable[[Update, CallbackContext], int]) -> typing.List[
    typing.Union[MessageHandler, CommandHandler]
]:
    res = [
            MessageHandler(Filters.text & ~Filters.command, callback=func),
    ]
    return res
