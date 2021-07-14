"""

"""

from __future__ import annotations

import enum
import typing

from constants import DEFAULT_DAYS_IN_FUTURE, MAX_USER_RULES_ALLOWED

__all__ = [
    "MenuItem", "MENU_LOCALIZATION",
    "Language",
]


class Language(enum.Enum):
    Russian = enum.auto()
    English = enum.auto()
    DemoEnglish = enum.auto()

    @classmethod
    def _flag_dict(cls) -> typing.Dict[Language, str]:
        res = {
            cls.English: "🇬🇧",
            cls.Russian: "🇷🇺",
        }
        return res

    @property
    def flag(self) -> typing.Union[str, None]:
        res = self._flag_dict().get(self)
        return res

    @classmethod
    def from_flag(cls, flag: str) -> Language:
        inv_flag_dict = {
            v: k
            for k, v in cls._flag_dict().items()
        }
        inst = inv_flag_dict[flag]
        return inst

    @classmethod
    def _str_dict(cls) -> typing.Dict[Language, str]:
        res = {
            cls.English: "en",
            cls.Russian: "ru",
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
        Language.English: "Done changing settings. If you wish to chanage settings once again - just call /menu",
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
        Language.Russian: "Некорректный домен. Попробуйте ещё раз.",
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
    MenuItem.ListSubscribedGames: {
        Language.Russian: "Игры в списке слежения",
        Language.English: "Tracked games",
    },
    MenuItem.NoSubscribedGames: {
        Language.Russian: "Вы пока не следите ни за одной игрой.",
        Language.English: "You are not following any games yet.",
    },
    MenuItem.GamesInFutureWarning: {
        Language.Russian: f"Показываю игры в ближайшие {DEFAULT_DAYS_IN_FUTURE} дней, на которые вы подписаны:",
        Language.English: f"Showing games you follow, that start within the next {DEFAULT_DAYS_IN_FUTURE} days:",
    },
    MenuItem.RuleLimitReached: {
        Language.Russian: f"""У вас не может быть больше {MAX_USER_RULES_ALLOWED} правил.
         Пожалуйста, удалите старые и неактуальные правила для добавления новых.""",
        Language.English: f"""You can't have more than {MAX_USER_RULES_ALLOWED} rules.
         Please, delete old and irrelevant rules to proceed.""",
    },
    MenuItem.ChangeParticipantsJoiner:
        {
            Language.Russian: ("\nНовых заявок: ", "\nСняли заявку: ", "\nВсего заявок: "),
            Language.English: ("\nNew participants: ", "\nDismissed participants: ", "\nTotal participants: "),
        },
    MenuItem.NewGame: {
        Language.Russian: "Новая игра",
        Language.English: "New game",
    },
    MenuItem.NameChanged: {
        Language.Russian: "Название игры изменилось",
        Language.English: "Game name changed",
    },
    MenuItem.StartTimeChanged: {
        Language.Russian: "Начало игры перенесено",
        Language.English: "Game start time changed",
    },
    MenuItem.EndTimeChanged: {
        Language.Russian: "Окончание игры перенесено",
        Language.English: "Game end time changed",
    },
    MenuItem.PassingSequenceChanged: {
        Language.Russian: "Последовательность прохождения игры изменилась",
        Language.English: "Game passing sequence changed",
    },
    MenuItem.PlayersListChanged: {
        Language.Russian: "Список участников изменился",
        Language.English: "Playsers list changed",
    },
    MenuItem.DescriptionChanged: {
        Language.Russian: "Описание игры изменилось",
        Language.English: "Game description changed",
    },
    MenuItem.NewForumMessage: {
        Language.Russian: "Новое сообщение(я) на форуме. Последнее сообщение",
        Language.English: "New forum message(ы). Last message",
    },
    MenuItem.PlayerIDText: {
        Language.Russian: "Игрок {id}",
        Language.English: "Player {id}",
    },
    MenuItem.TeamIDText: {
        Language.Russian: "Команда {id}",
        Language.English: "Team {id}",
    },
    MenuItem.GameIDText: {
        Language.Russian: "Игра {id}",
        Language.English: "Game {id})",
    },
    MenuItem.InDomainText: {
        Language.Russian: "в домене",
        Language.English: "in domain",
    },
    MenuItem.LinkText: {
        Language.Russian: "ссылка",
        Language.English: "link",
    },
    MenuItem.DomainText: {
        Language.Russian: "Домен",
        Language.English: "Domain",
    },
    MenuItem.ForumText: {
        Language.Russian: "Форум",
        Language.English: "Forum",
    },
    MenuItem.AuthorsText: {
        Language.Russian: "Автор(ы)",
        Language.English: "Author(s)",
    },
    MenuItem.TimeFromToText: {
        Language.Russian: ["С", "по"],
        Language.English: ["From", "to"],
    },
    MenuItem.DescriptionText: {
        Language.Russian: "Описание",
        Language.English: "Description",
    },
    MenuItem.UpdateText: {
        Language.Russian: "Обновление по игре",
        Language.English: "Game update for"
    },
    MenuItem.GameModeQuest: {
        Language.Russian: "Схватка",
        Language.English: "Quest",
        Language.DemoEnglish: "Real",
    },
    MenuItem.GameModePoints: {
        Language.Russian: "Точки",
        Language.English: "Points",
    },
    MenuItem.GameModeBrainstorm: {
        Language.Russian: "Мозговой штурм",
        Language.English: "Brainstorm",
        Language.DemoEnglish: "Brainstorming",
    },
    MenuItem.GameModeQuiz: {
        Language.Russian: "Викторина",
        Language.English: "Quiz",
    },
    MenuItem.GameModePhotoHunt: {
        Language.Russian: "Фотоохота",
        Language.English: "PhotoHunt",
    },
    MenuItem.GameModePhotoExtreme: {
        Language.Russian: "Фотоэкстрим",
        Language.English: "PhotoExtreme",
    },
    MenuItem.GameModeGeoCaching: {
        Language.Russian: "Кэшинг",
        Language.English: "GeoCaching",
    },
    MenuItem.GameModeWetWars: {
        Language.Russian: "Мокрые войны",
        Language.English: "WetWars",
    },
    MenuItem.GameModeCompetition: {
        Language.Russian: "Конкурс",
        Language.English: "Competition",
    },
    MenuItem.GameFormatSingle: {
        Language.Russian: "В одиночку",
        Language.English: "Single",
    },
    MenuItem.GameFormatTeam: {
        Language.Russian: "Командами",
        Language.English: "Team",
    },
    MenuItem.GameFormatPersonal: {
        Language.Russian: "Персонально",
        Language.English: "Personal",
        Language.DemoEnglish: "Personal(she)",
    },
    MenuItem.GameFormatMembersSingle: {
        Language.Russian: "Игроков зарегистрировано",
        Language.English: "Players registered",
    },
    MenuItem.GameFormatMembersTeam: {
        Language.Russian: "Команд зарегистрировано",
        Language.English: "Teams registered",
    },
    MenuItem.GameFormatMembersPersonal: {
        Language.Russian: "Игроков зарегистрировано",
        Language.English: "Players registered",
    },

    MenuItem.PassingSequenceLinear: {
        Language.Russian: "Линейная",
        Language.English: "Linear",
    },
    MenuItem.PassingSequenceStorm: {
        Language.Russian: "Штурмовая",
        Language.English: "Storm",
    },
    MenuItem.PassingSequenceCustom: {
        Language.Russian: "Указанная (не линейная)",
        Language.English: "Custom (not linear)",
    },
    MenuItem.PassingSequenceRandom: {
        Language.Russian: "Случайная",
        Language.English: "Random",
    },
    MenuItem.PassingSequenceDynamicallyRandom: {
        Language.Russian: "Динамически случайная",
        Language.English: "Dinamically random",
    },
    MenuItem.DescriptionBeforeAfter: {
        Language.Russian: ["Старое описание", "Новое описание"],
        Language.English: ["Old description", "New description"],
    },
}
