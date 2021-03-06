"""

"""

from __future__ import annotations

import enum
import typing

from meta_constants import DEFAULT_DAYS_IN_FUTURE, MAX_USER_RULES_ALLOWED

__all__ = [
    "MenuItem", "MENU_LOCALIZATION",
    "Language",
]


class Language(enum.Enum):
    Russian = enum.auto()
    English = enum.auto()
    Ukrainian = enum.auto()
    DemoEnglish = enum.auto()
    QuestRussian = enum.auto()

    @classmethod
    def _str_dict(cls) -> typing.Dict[Language, str]:
        res = {
            cls.English: "en",
            cls.Russian: "ru",
            cls.Ukrainian: "uk",
        }
        return res

    def to_str(self) -> str:
        res = self._str_dict()[self]
        return res

    @classmethod
    def from_str(cls, s: str) -> Language:
        inv_di = {
            v: k
            for k, v in cls._str_dict().items()
        }
        inv_di[""] = Language.Russian
        inst = inv_di[s]
        return inst

    @classmethod
    def full_name_dict(cls) -> typing.Dict[Language, str]:
        di = {
            cls.English: "English",
            cls.Ukrainian: "Українська",
            cls.Russian: "Русский",
        }
        return di

    @classmethod
    def from_full_name(cls, full_name: str) -> Language:
        inv_di = {
            v: k
            for k, v in cls.full_name_dict().items()
        }
        inst = inv_di.get(full_name, cls.English)
        return inst

    @property
    def full_name(self) -> str:
        return self.full_name_dict()[self]


class MenuItem(enum.Enum):
    LangSet = enum.auto()
    MainMenu = enum.auto()
    Error = enum.auto()
    Info = enum.auto()
    UpdatesOn = enum.auto()
    UpdatesOff = enum.auto()
    BotStopped = enum.auto()
    Help = enum.auto()
    AddRule = enum.auto()
    DeleteRule = enum.auto()
    ListRules = enum.auto()
    MenuNoAction = enum.auto()
    MenuChoiceIncorrect = enum.auto()
    Welcome = enum.auto()
    MenuEnd = enum.auto()
    DomainRule = enum.auto()
    GameRule = enum.auto()
    AuthorRule = enum.auto()
    GameIgnoreRule = enum.auto()
    PlayerRule = enum.auto()
    TeamRule = enum.auto()
    RuleTypeChoiceMenu = enum.auto()
    DomainPrompt = enum.auto()
    RuleAdded = enum.auto()
    RuleNotAdded = enum.auto()
    DomainChoicePrompt = enum.auto()
    GameIDPrompt = enum.auto()
    GameIgnoreIDPrompt = enum.auto()
    DomainEmptyError = enum.auto()
    IDInvalid = enum.auto()
    NoRules = enum.auto()
    ChooseRuleToDelete = enum.auto()
    RuleIDInvalid = enum.auto()
    RuleDeleted = enum.auto()
    AnotherDomain = enum.auto()
    RoughRuleDescription = enum.auto()
    GranularRuleDescription = enum.auto()
    IgnoreRuleDescription = enum.auto()
    DomainInvalid = enum.auto()
    TeamIDPrompt = enum.auto()
    PlayerIDPrompt = enum.auto()
    AuthorIDPrompt = enum.auto()
    ListSubscribedGames = enum.auto()
    NoSubscribedGames = enum.auto()
    GamesInFutureWarning = enum.auto()
    RuleLimitReached = enum.auto()
    ChangeParticipantsJoiner = enum.auto()

    NewGame = enum.auto()
    NameChanged = enum.auto()
    PassingSequenceChanged = enum.auto()
    StartTimeChanged = enum.auto()
    EndTimeChanged = enum.auto()
    PlayersListChanged = enum.auto()
    DescriptionChanged = enum.auto()
    NewForumMessage = enum.auto()

    PlayerIDText = enum.auto()
    TeamIDText = enum.auto()
    GameIDText = enum.auto()
    AuthorIDText = enum.auto()
    GameIgnoreIDText = enum.auto()

    InDomainText = enum.auto()
    LinkText = enum.auto()
    DomainText = enum.auto()
    ForumText = enum.auto()
    AuthorsText = enum.auto()
    TimeFromToText = enum.auto()
    DescriptionText = enum.auto()
    UpdateText = enum.auto()

    GameModeQuest = enum.auto()
    GameModePoints = enum.auto()
    GameModeBrainstorm = enum.auto()
    GameModeQuiz = enum.auto()
    GameModePhotoHunt = enum.auto()
    GameModePhotoExtreme = enum.auto()
    GameModeGeoCaching = enum.auto()
    GameModeWetWars = enum.auto()
    GameModeCompetition = enum.auto()

    GameFormatSingle = enum.auto()
    GameFormatTeam = enum.auto()
    GameFormatPersonal = enum.auto()

    GameFormatMembersSingle = enum.auto()
    GameFormatMembersTeam = enum.auto()
    GameFormatMembersPersonal = enum.auto()

    PassingSequenceLinear = enum.auto()
    PassingSequenceStorm = enum.auto()
    PassingSequenceCustom = enum.auto()
    PassingSequenceRandom = enum.auto()
    PassingSequenceDynamicallyRandom = enum.auto()

    DescriptionBeforeAfter = enum.auto()
    BotStatusReportAllowed = enum.auto()
    BotStatusReportNotAllowed = enum.auto()

    DontUnderstand = enum.auto()
    TUYears = enum.auto()
    TUMonths = enum.auto()
    TUDays = enum.auto()
    TUHours = enum.auto()
    TUMinutes = enum.auto()
    TUSeconds = enum.auto()
    TUBy = enum.auto()
    TUForward = enum.auto()
    TUBackward = enum.auto()


MENU_LOCALIZATION = {
    MenuItem.LangSet: {
        Language.Russian: "Язык успешно установлен: {}",
        Language.English: "Language successfully set: {}",
        Language.Ukrainian: "Мову успішно встановлено: {}",
    },
    MenuItem.MainMenu: {
        Language.Russian: "Что бы вы хотели сделать?",
        Language.English: "Would you like to do?",
        Language.Ukrainian: "Що б ви хотіли зробити?",
    },
    MenuItem.Error: {
        Language.Russian: "Произошла ошибка:",
        Language.English: "An error occurred:",
        Language.Ukrainian: "Сталась помилка",
    },
    MenuItem.Info: {
        Language.Russian: "Это новостной бот сети квестов QEng\nВерсия {}\nВаш язык - Русский\nОповещения {}",
        Language.English: "This is a news bot for the network of urban games QEng\nVersion {}\nYour language is English"
                          "\nUpdates are {}",
        Language.Ukrainian: "Це новинний бот мережі ігр QEng\nВерсія {}\nВаша мова - Українська\nСповіщення {}",
    },
    MenuItem.UpdatesOn: {
        Language.Russian: f"включены {chr(0x2705)}",
        Language.English: f"on {chr(0x2705)}",
        Language.Ukrainian: f"ввімкені {chr(0x2705)}",
    },
    MenuItem.UpdatesOff: {
        Language.Russian: f"отключены {chr(0x274C)}",
        Language.English: f"off {chr(0x274C)}",
        Language.Ukrainian: f"вимкені {chr(0x274C)}",
    },
    MenuItem.BotStopped: {
        Language.Russian: "Я больше не буду слать вам уведомления. Если вы захотите возобновить обновления - "
                          "пришлите мне команду /start",
        Language.English: "I won't send you updates anymore. If you'd like to resume receiving game news - just "
                          "send me the /start command",
        Language.Ukrainian: "Я більше не буду надсилати вам сповіщення. Якщо ви захочете відновити оновлення - "
                          "надішліть мені команду /start",
    },
    MenuItem.Help: {
        Language.Russian: "Прочитать информацию о боте можно "
                          "<a href='https://telegra.ph/Encounter-News---Bot-09-20' target='_blank'>тут</a>",
        Language.English: "Read up more about this bot "
                          "<a href='https://telegra.ph/Encounter-News---Bot-English-09-20' target='_blank'>here</a>",
        Language.Ukrainian: "Прочитати інформацію про бота можна "
                            "<a href='https://telegra.ph/Encounter-News---Bot-Ukrainian-09-20' target='_blank'>тут</a>",
    },
    MenuItem.Welcome: {
        Language.Russian: """
        Приветствую! Я - бот, который поможет вам всегда быть в курсе 
        всех новостей QEng. Я могу следить за всеми играми на определённом домене, за какой-то конкретной игрой 
        или за всеми играми вашей команды.
        Когда на сайте будут какие-то изменения в анонсе игры, или появятся новые игры - 
        я обязательно вам об этом сообщу. 
        Прочитайте моё описание <a href='https://telegra.ph/Encounter-News---Bot-09-20' target='_blank'>тут</a>.
         Сейчас рекомендую добавить ваше первое правило отслеживания домена.""",
        Language.English: """
        Hello! I am a bot who will help you always be up-to-date 
        with all QEng games. I can track all games in a given domain, track a certain game, or
         track all games where your team (or you) participates. When there are any changes to a game announcement,
         or there's a new game going on - I'll send you a message.
          Read my description <a href='https://telegra.ph/Encounter-News---Bot-English-09-20' 
          target='_blank'>here</a>. 
          Now I suggest you add your first domain tracking rule.""",
        Language.Ukrainian: """
        Привіт! Я - бот, що допоможе вам завжди бути в курсі всіх новин ігр QEng.
        Я можу стежити за всіма іграми на визначеному домені, за якосюсь конкретною грою, 
        чи за всіма іграми вашої команди. Коли на сайті ставатимуться якісь зміни в анонсі гри, чи з'являться 
        нові ігри - я обов'язково вам про це повідомлю. 
        Прочитайте мій опис <a href='https://telegra.ph/Encounter-News---Bot-Ukrainian-09-20' target='_blank'>тут</a>.
         Зараз рекомендую вам додати ваше перше правило відстежування домену.""",
    },
    MenuItem.AddRule: {
        Language.Russian: "Добавить правило слежения",
        Language.English: "Add tracking rule",
        Language.Ukrainian: "Додати правило стеження",
    },
    MenuItem.DeleteRule: {
        Language.Russian: "Удалить правило слежения",
        Language.English: "Delete tracking rule",
        Language.Ukrainian: "Видалити правило стеження",
    },
    MenuItem.ListRules: {
        Language.Russian: "Показать список правил слежения",
        Language.English: "List tracking rules",
        Language.Ukrainian: "Показати список правил стеження",
    },
    MenuItem.MenuChoiceIncorrect: {
        Language.Russian: "Неправильный выбор! Попробуйте ещё раз.",
        Language.English: "Incorrect choice. Try again.",
        Language.Ukrainian: "Невірний вибір! Спробуйте ще.",
    },
    MenuItem.MenuEnd: {
        Language.Russian: "Выбор настроек окончен. Если хотите совершить настройку ещё раз - вызовите комманду /menu. "
                          "Если вы только что вызывали какую-то из / команд - попробуйте повторить",
        Language.English: "Done changing settings. If you wish to chanage settings once again - just call /menu",
        Language.Ukrainian: "Налаштування завершено. Якщо захочете повернутись до процесу налаштування -"
                            " викличте команду /menu",
    },
    MenuItem.DomainRule: {
        Language.Russian: "Слежение за доменом",
        Language.English: "Whole domain tracking",
        Language.Ukrainian: "Стеження за доменом",
    },
    MenuItem.GameRule: {
        Language.Russian: "Слежение за отдельной игрой в домене",
        Language.English: "Single game tracking (within one domain)",
        Language.Ukrainian: "Стеження за окремою грою в домені",
    },
    MenuItem.AuthorRule: {
        Language.Russian: "Слежение за всеми играми автора в домене",
        Language.English: "Single author tracking (within one domain)",
        Language.Ukrainian: "Стеження за всіма іграми автора в домені",
    },
    MenuItem.GameIgnoreRule: {
        Language.Russian: "Игнорирование игры в домене",
        Language.English: "Single game ignoring (within one domain)",
        Language.Ukrainian: "Ігнорування гри в домені",
    },
    MenuItem.TeamRule: {
        Language.Russian: "Слежение за играми команды в домене",
        Language.English: "Single team games tracking (within one domain)",
        Language.Ukrainian: "Стеження за іграми команди в домені",
    },
    MenuItem.PlayerRule: {
        Language.Russian: "Слежение за играми конкретного игрока в домене (для одиночных игр)",
        Language.English: "Specific player games tracking (within one domain) (for single games)",
        Language.Ukrainian: "Стеження за іграми конкретного гравця в домені (для одиночних ігр)",
    },
    MenuItem.RuleTypeChoiceMenu: {
        Language.Russian: "Выберите тип правила слежения",
        Language.English: "Choose tracking rule type",
        Language.Ukrainian: "Оберіть тип правила стеження",
    },
    MenuItem.DomainPrompt: {
        Language.Russian: """
        Пришлите мне ссылку на домен. Например, https://game.qeng.org/.
        Поддерживаются домены *.qeng.org""",
        Language.English: """
        Send me domain URL. E.g. https://game.qeng.org/.
        Domains supported are *.qeng.org""",
        Language.Ukrainian: """
        Надішліть мені посилання на домен. Наприклад, https://game.qeng.org/.
        Домени, що підтримуються: *.qeng.org""",
    },
    MenuItem.RoughRuleDescription: {
        Language.Russian: """
        Я буду присылать вам только важные новости: перенос игры или большое изменение в описании. 
         Мелкие изменения я отслеживаю только в командных / индивидуальных / игровых правилах.""",
        Language.English: """
        I will send you only important updates: when game dates changed or if
         there is a major change in a game description. Minor changes are only tracked
         under team / individual / game rules.""",
        Language.Ukrainian: """
        Я буду надсилати вам тільки важливі новини: про перенесення гри чи дійсно великі зміни в описі гри.
         Дрібні зміни я відстежую тільки в командних / індивідуальних / ігрових правилах."""
    },

    MenuItem.RuleAdded: {
        Language.Russian: "Правило\n{}\nдобавлено успешно",
        Language.English: "Rule\n{}\nadded successfully",
        Language.Ukrainian: "Правило\n{}\nдодано успішно",
    },
    MenuItem.RuleNotAdded: {
        Language.Russian: "Правило\n{}\nуже находится в вашем списке правил",
        Language.English: "Rule\n{}\nalready exists in your rule list",
        Language.Ukrainian: "Правило\n{}\nвже знаходиться у вашому списку правил",
    },
    MenuItem.DomainChoicePrompt: {
        Language.Russian: "Выберите домен",
        Language.English: "Choose domain",
        Language.Ukrainian: "Оберіть домен",
    },
    MenuItem.GameIDPrompt: {
        Language.Russian: """
        Пришлите ID игры, которую вы хотите отслеживать. 
         Например, для игры https://game.qeng.org/archive.php?gid=4329 ID будет 4329""",
        Language.English: """
        Send game ID you wish to track. 
         E.g. for game https://game.qeng.org/archive.php?gid=4329, ID is 4329""",
        Language.Ukrainian: """
        Надішліть ID гри, яку ви хочете відстежувати.
         Наприклад, для гри https://game.qeng.org/archive.php?gid=4329 ID буде 4329"""
    },
    MenuItem.GameIgnoreIDPrompt: {
        Language.Russian: """
        Пришлите ID игры, которую вы хотите игнорировать. 
         Например, для игры https://game.qeng.org/archive.php?gid=4329 ID будет 4329""",
        Language.English: """
        Send game ID you wish to ignore. 
         E.g. for game https://game.qeng.org/archive.php?gid=4329, ID is 4329""",
        Language.Ukrainian: """
        Надішліть ID гри, яку ви хочете ігнорувати.
         Наприклад, для гри https://game.qeng.org/archive.php?gid=4329 ID буде 4329"""
    },
    MenuItem.DomainEmptyError: {
        Language.Russian: "Не могу определить название домена. Попробуйте сначала.",
        Language.English: "Can't get domain name. Please, try again.",
        Language.Ukrainian: "Не можу визначити назву домена. Спробуйте спочатку.",
    },
    MenuItem.IDInvalid: {
        Language.Russian: "ID неправильный. Попробуйте сначала.",
        Language.English: "ID is invalid. Please, try again.",
        Language.Ukrainian: "ID невірний. Спробуйте спочатку.",
    },
    MenuItem.NoRules: {
        Language.Russian: "У вас пока нет правил",
        Language.English: "You don't have any rules just yet",
        Language.Ukrainian: "У вас поки нема правил",
    },
    MenuItem.MenuNoAction: {
        Language.Russian: "Ничего",
        Language.English: "Nothing",
        Language.Ukrainian: "Нічого",
    },
    MenuItem.ChooseRuleToDelete: {
        Language.Russian: "Выберите правило, которое хотите удалить",
        Language.English: "Choose rule you want to delete",
        Language.Ukrainian: "Оберіть правило, яке хочете видалити",
    },
    MenuItem.RuleIDInvalid: {
        Language.Russian: "ID правила неверный. Попробуйте сначала.",
        Language.English: "Rule ID invalid. Please, try again.",
        Language.Ukrainian: "ID правила невірний. Спробуйте спочатку.",
    },
    MenuItem.RuleDeleted: {
        Language.Russian: "Правило\n{}\nудалено успешно.",
        Language.English: "Rule\n{}\ndeleted successfully.",
        Language.Ukrainian: "Правило\n{}\nвидалено успішно.",
    },
    MenuItem.AnotherDomain: {
        Language.Russian: "Другой домен",
        Language.English: "Another domain",
        Language.Ukrainian: "Інший домен",
    },
    MenuItem.GranularRuleDescription: {
        Language.Russian: """
        Я буду присылать вам все новости: перенос игры, любое изменение в описании игры, новое сообщение на форуме.
         Также с этим правилом вы можете следить за играми без отслеживания всего домена целиком.""",
        Language.English: """
        I will send you all updates: when game dates changed, if there's any change in a game description,
        or when there's a new forum post.
         With this rule you can also track games without tracking the whole domain.""",
        Language.Ukrainian: """
        Я надсилатиму вам всі новини: про перенесення гри, про будь-які зміни в описі гри, чи коли з'являється
         нове повідомлення на форумі. Також з цим правилом ви можете стежити за грою без відстеження 
         всього домена цілком.""",
    },
    MenuItem.IgnoreRuleDescription: {
        Language.Russian: """
        Я НЕ буду присылать вам никакие новости по выбранной игре""",
        Language.English: """
        I will NOT send you any updates on the game you choose""",
        Language.Ukrainian: """
        Я НЕ буду надсилати вам ніякі новини по обраній грі""",
    },
    MenuItem.DomainInvalid: {
        Language.Russian: "Некорректный домен. Попробуйте ещё раз.",
        Language.English: "Invalid domain. Try again.",
        Language.Ukrainian: "Невірний домен. Спробуйте ще",
    },
    MenuItem.TeamIDPrompt: {
        Language.Russian: """
    Пришлите ID команды, игры которой вы хотите отслеживать. 
     Например, для команды https://game.qeng.org/team.php?team_id=4048 ID будет 4048""",
        Language.English: """
    Send team ID you wish to follow. 
     E.g. for team https://game.qeng.org/team.php?team_id=4048, ID is 4048""",
        Language.Ukrainian: """
        Надішліть ID команди, ігри якої ви хочете відстежувати.
         Наприклад, для команди https://game.qeng.org/team.php?team_id=4048 ID буде 4048""",
    },
    MenuItem.PlayerIDPrompt: {
        Language.Russian: """
    Пришлите ID игрока, игры которого вы хотите отслеживать (для одиночных игр).  
     Например, для игрока https://game.qeng.org/view_user.php?user_id=9856 ID будет 9856""",
        Language.English: """
    Send player ID you wish to follow (for single games). 
     E.g. for player https://game.qeng.org/view_user.php?user_id=9856, ID is 9856""",
        Language.Ukrainian: """
        Надішліть ID гравця, ігри якого ви хочете відстежувати.
         Наприклад, для гравця https://game.qeng.org/view_user.php?user_id=9856, ID буде 9856""",
    },

    MenuItem.AuthorIDPrompt: {
        Language.Russian: """
    Пришлите ID автора, игры которого вы хотите отслеживать.  
     Например, для игрока https://game.qeng.org/view_user.php?user_id=9856 ID будет 9856""",
        Language.English: """
    Send player ID you wish to follow (as an author). 
     E.g. for player https://game.qeng.org/view_user.php?user_id=9856, ID is 9856""",
        Language.Ukrainian: """
        Надішліть ID автора, ігри якого ви хочете відстежувати.
         Наприклад, для гравця https://game.qeng.org/view_user.php?user_id=9856, ID буде 9856""",
    },

    MenuItem.ListSubscribedGames: {
        Language.Russian: "Игры в списке слежения",
        Language.English: "Tracked games",
        Language.Ukrainian: "Ігри в списку відстеження",
    },
    MenuItem.NoSubscribedGames: {
        Language.Russian: "Вы пока не следите ни за одной игрой.",
        Language.English: "You are not following any games yet.",
        Language.Ukrainian: "Ви поки що не відстежуєте жодну гру.",
    },
    MenuItem.GamesInFutureWarning: {
        Language.Russian: f"Показываю игры в ближайшие {DEFAULT_DAYS_IN_FUTURE} дней, на которые вы подписаны:",
        Language.English: f"Showing games you follow, that start within the next {DEFAULT_DAYS_IN_FUTURE} days:",
        Language.Ukrainian: f"Показую ігри в найближчі {DEFAULT_DAYS_IN_FUTURE} днів, що ви підписані на них",
    },
    MenuItem.RuleLimitReached: {
        Language.Russian: f"""
        У вас не может быть больше {MAX_USER_RULES_ALLOWED} правил.
         Пожалуйста, удалите старые и неактуальные правила для добавления новых.""",
        Language.English: f"""
        You can't have more than {MAX_USER_RULES_ALLOWED} rules.
         Please, delete old and irrelevant rules to proceed.""",
        Language.Ukrainian: f"""
        Ви не можете мати більше, ніж {MAX_USER_RULES_ALLOWED} правил.
         Будь ласка, видаліть старі та неактуальні правила, щоб додавати нові.""",
    },
    MenuItem.ChangeParticipantsJoiner:
        {
            Language.Russian: (
                "Новых заявок: {n_new} {new}",
                "Сняли заявку: {n_dropped} {dropped}",
                "Всего заявок: {tot}",
            ),
            Language.English: (
                "New participants: {n_new} {new}",
                "Dismissed participants: {n_dropped} {dropped}",
                "Total participants: {tot}"
            ),
            Language.Ukrainian: (
                "Нових заявок: {n_new} {new}",
                "Зняли заявку: {n_dropped} {dropped}",
                "Всього заявок: {tot}",
            ),
        },
    MenuItem.NewGame: {
        Language.Russian: "Новая игра",
        Language.English: "New game",
        Language.Ukrainian: "Нова гра",
    },
    MenuItem.NameChanged: {
        Language.Russian: "Название игры изменилось",
        Language.English: "Game name changed",
        Language.Ukrainian: "Назва гри змінилась",
    },
    MenuItem.StartTimeChanged: {
        Language.Russian: "Начало игры перенесено",
        Language.English: "Game start time changed",
        Language.Ukrainian: "Початок гри перенесено",
    },
    MenuItem.EndTimeChanged: {
        Language.Russian: "Окончание игры перенесено",
        Language.English: "Game end time changed",
        Language.Ukrainian: "Закінчення гри перенесено",
    },
    MenuItem.PassingSequenceChanged: {
        Language.Russian: "Последовательность прохождения игры изменилась",
        Language.English: "Game passing sequence changed",
        Language.Ukrainian: "Послідовність проходження гри змінилась",
    },
    MenuItem.PlayersListChanged: {
        Language.Russian: "Список участников изменился",
        Language.English: "Players list changed",
        Language.Ukrainian: "Список гравців змінився",
    },
    MenuItem.DescriptionChanged: {
        Language.Russian: "Описание игры изменилось",
        Language.English: "Game description changed",
        Language.Ukrainian: "Опис гри змінився",
    },
    MenuItem.NewForumMessage: {
        Language.Russian: "Новое сообщение(я) на форуме. Последнее сообщение",
        Language.English: "New forum message(s). Last message",
        Language.Ukrainian: "Нове(і) повідомлення на форумі. Останнє повідомлення",
    },
    MenuItem.PlayerIDText: {
        Language.Russian: "Игрок {id}",
        Language.English: "Player {id}",
        Language.Ukrainian: "Гравець {id}",
    },
    MenuItem.TeamIDText: {
        Language.Russian: "Команда {id}",
        Language.English: "Team {id}",
        Language.Ukrainian: "Команда {id}",
    },
    MenuItem.GameIDText: {
        Language.Russian: "Игра {id}",
        Language.English: "Game {id})",
        Language.Ukrainian: "Гра {id}",
    },
    MenuItem.AuthorIDText: {
        Language.Russian: "Автор {id}",
        Language.English: "Author {id})",
        Language.Ukrainian: "Автор {id}",
    },
    MenuItem.GameIgnoreIDText: {
        Language.Russian: "Игнор игры {id}",
        Language.English: "Ignore game {id})",
        Language.Ukrainian: "Ігнор гри {id}",
    },
    MenuItem.InDomainText: {
        Language.Russian: "в домене",
        Language.English: "in domain",
        Language.Ukrainian: "в домені",
    },
    MenuItem.LinkText: {
        Language.Russian: "ссылка",
        Language.English: "link",
        Language.Ukrainian: "посилання",
    },
    MenuItem.DomainText: {
        Language.Russian: "Домен",
        Language.English: "Domain",
        Language.Ukrainian: "Домен",
    },
    MenuItem.ForumText: {
        Language.Russian: "Форум",
        Language.English: "Forum",
        Language.Ukrainian: "Форум",
    },
    MenuItem.AuthorsText: {
        Language.Russian: "Автор(ы)",
        Language.English: "Author(s)",
        Language.Ukrainian: "Автор(и)",
    },
    MenuItem.TimeFromToText: {
        Language.Russian: ["С", "по"],
        Language.English: ["From", "to"],
        Language.Ukrainian: ["З", "по"],
    },
    MenuItem.DescriptionText: {
        Language.Russian: "Описание",
        Language.English: "Description",
        Language.Ukrainian: "Опис гри"
    },
    MenuItem.UpdateText: {
        Language.Russian: "Обновление по игре",
        Language.English: "Game update for",
        Language.Ukrainian: "Оновлення у грі",
    },
    MenuItem.GameModeQuest: {
        Language.Russian: "Схватка",
        Language.English: "Quest",
        Language.DemoEnglish: "Real",
        Language.Ukrainian: "Сутичка",
        Language.QuestRussian: "Квест",
    },
    MenuItem.GameModePoints: {
        Language.Russian: "Точки",
        Language.English: "Points",
        Language.Ukrainian: "Точки",
        Language.QuestRussian: "ЛайтКвест",
    },
    MenuItem.GameModeBrainstorm: {
        Language.Russian: "Мозговой штурм",
        Language.English: "Brainstorm",
        Language.DemoEnglish: "Brainstorming",
        Language.Ukrainian: "Мозковий штурм",
        Language.QuestRussian: "Онлайн игры",
    },
    MenuItem.GameModeQuiz: {
        Language.Russian: "Викторина",
        Language.English: "Quiz",
        Language.Ukrainian: "Quiz",
    },
    MenuItem.GameModePhotoHunt: {
        Language.Russian: "Фотоохота",
        Language.English: "PhotoHunt",
        Language.Ukrainian: "Фотополювання",
    },
    MenuItem.GameModePhotoExtreme: {
        Language.Russian: "Фотоэкстрим",
        Language.English: "PhotoExtreme",
        Language.Ukrainian: "Фотоекстрім",
    },
    MenuItem.GameModeGeoCaching: {
        Language.Russian: "Кэшинг",
        Language.English: "GeoCaching",
        Language.Ukrainian: "Кешинг",
    },
    MenuItem.GameModeWetWars: {
        Language.Russian: "Мокрые войны",
        Language.English: "WetWars",
        Language.Ukrainian: "Мокрі війни",
    },
    MenuItem.GameModeCompetition: {
        Language.Russian: "Конкурс",
        Language.English: "Competition",
        Language.Ukrainian: "Competition",
    },
    MenuItem.GameFormatSingle: {
        Language.Russian: "В одиночку",
        Language.English: "Single",
        Language.Ukrainian: "Поодинці",
    },
    MenuItem.GameFormatTeam: {
        Language.Russian: "Командами",
        Language.English: "Team",
        Language.Ukrainian: "Командами",
    },
    MenuItem.GameFormatPersonal: {
        Language.Russian: "Персонально",
        Language.English: "Personal",
        Language.DemoEnglish: "Personal(she)",
        Language.Ukrainian: "Персонально",
    },
    MenuItem.GameFormatMembersSingle: {
        Language.Russian: "Игроков зарегистрировано",
        Language.English: "Players registered",
        Language.Ukrainian: "Гравців зареєстровано",
    },
    MenuItem.GameFormatMembersTeam: {
        Language.Russian: "Команд зарегистрировано",
        Language.English: "Teams registered",
        Language.Ukrainian: "Команд зареєстровано",
    },
    MenuItem.GameFormatMembersPersonal: {
        Language.Russian: "Игроков зарегистрировано",
        Language.English: "Players registered",
        Language.Ukrainian: "Гравців зареєстровано",
    },

    MenuItem.PassingSequenceLinear: {
        Language.Russian: "Линейная",
        Language.English: "Linear",
        Language.Ukrainian: "Послідовна",
    },
    MenuItem.PassingSequenceStorm: {
        Language.Russian: "Штурмовая",
        Language.English: "Storm",
        Language.Ukrainian: "Штурмова",
    },
    MenuItem.PassingSequenceCustom: {
        Language.Russian: "Указанная (не линейная)",
        Language.English: "Custom (not linear)",
        Language.Ukrainian: "Вказана автором (не послідовна)",
    },
    MenuItem.PassingSequenceRandom: {
        Language.Russian: "Случайная",
        Language.English: "Random",
        Language.Ukrainian: "Випадкова",
    },
    MenuItem.PassingSequenceDynamicallyRandom: {
        Language.Russian: "Динамически случайная",
        Language.English: "Dinamically random",
        Language.Ukrainian: "Динамічно випадкова",
    },
    MenuItem.DescriptionBeforeAfter: {
        Language.Russian: ["Старое описание", "Новое описание"],
        Language.English: ["Old description", "New description"],
        Language.Ukrainian: ["Старий опис", "Новий опис"],
    },
    MenuItem.BotStatusReportAllowed: {
        Language.Russian: "Статус (за последние 24 часа):\n{} сообщений отправлено\n{} сообщений доставлено",
        Language.English: "Status (in the last 24 hours):\n{} messages sent\n{} messages delivered",
        Language.Ukrainian: "Статус (за останні 24 години):\n{} повідомлень відправлено\n{} повідомлень доставлено",
    },
    MenuItem.BotStatusReportNotAllowed: {
        Language.Russian: "Вы не имеете доступа к этой функции",
        Language.English: "You don't have access to this functionality",
        Language.Ukrainian: "Ви не маєте доступу до цієї функції",
    },
    MenuItem.DontUnderstand: {
        Language.Russian: "Я не понял вас. Если вы использовали команду из меню - то, возможно, меня перезапустили, "
                          "и я потерял нить общения. В этом случае попробуйте вызвать /menu ещё раз.",
        Language.English: "I didn't understand you. If you just used a menu command - then maybe I got rebooted and "
                          "lost the conversation thread. In this case, please, try calling /menu again.",
        Language.Ukrainian: "Я вас не зрозумів. Якщо ви використовували команду з меню - то, можливо, "
                            "мене перезапустили, і я забув, про що ми спілкувались. В цьому випадку спробуйте "
                            "викликати /menu ще раз.",
    },
    MenuItem.TUYears: {
        Language.Russian: "год",
        Language.English: "yrs",
        Language.Ukrainian: "рік",
    },
    MenuItem.TUMonths: {
        Language.Russian: "мес",
        Language.English: "mos",
        Language.Ukrainian: "міс",
    },
    MenuItem.TUDays: {
        Language.Russian: "дн",
        Language.English: "dys",
        Language.Ukrainian: "дн",
    },
    MenuItem.TUHours: {
        Language.Russian: "час",
        Language.English: "hr",
        Language.Ukrainian: "год",
    },
    MenuItem.TUMinutes: {
        Language.Russian: "мин",
        Language.English: "min",
        Language.Ukrainian: "хв",
    },
    MenuItem.TUSeconds: {
        Language.Russian: "сек",
        Language.English: "sec",
        Language.Ukrainian: "сек",
    },
    MenuItem.TUBy: {
        Language.Russian: "на",
        Language.English: "",
        Language.Ukrainian: "на",
    },
    MenuItem.TUBackward: {
        Language.Russian: "раньше",
        Language.English: "earlier",
        Language.Ukrainian: "раніше",
    },
    MenuItem.TUForward: {
        Language.Russian: "позже",
        Language.English: "later",
        Language.Ukrainian: "пізніше",
    },
}
