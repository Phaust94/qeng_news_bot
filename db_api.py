"""
DB API for the bot
"""

from __future__ import annotations

from sqlite3 import connect, Connection
from dataclasses import dataclass, field
import typing
import os
import datetime
from sqlite3 import IntegrityError

import pandas as pd

from meta import Domain, EncounterGame, Rule, GameFormat, Language, Update
from constants import PERCENTAGE_CHANGE_TO_TRIGGER, MAX_DESCRIPTION_LENGTH, MAX_LAST_MESSAGE_LENGTH,\
    InvalidDomainError, MAX_USER_RULES_ALLOWED, UPDATE_FREQUENCY_SECONDS, MIN_HOURS_GAME_CHANGE_NOTIFY

__all__ = [
    "EncounterNewsDB",
]

ADMIN_ID = 476001386

TIME_TO_SECONDS_FORMAT = "%Y-%m-%d %H:%M:%S"

N_SIGMA = 1


@dataclass
class EncounterNewsDB:
    db_location: str
    _db_conn: Connection = field(init=False, default=None)

    def __post_init__(self):
        db_exists = os.path.exists(self.db_location)
        self._db_conn = connect(self.db_location)
        if not db_exists:
            self.create_tables()

    def create_tables(self) -> None:
        self.query("""
        CREATE TABLE USER_SUBSCRIPTION
        (
        USER_ID int,
        RULE_ID varchar(10),
        RULE_ADDED_DATE TIMESTAMP_NTZ,
        PRIMARY KEY (USER_ID, RULE_ID)
        )
        """, raise_on_error=False)

        self.query("""
                CREATE TABLE RULE_DESCRIPTION
                (
                RULE_ID varchar(10),
                DOMAIN varchar(100),
                PLAYER_ID int,
                TEAM_ID int,
                GAME_ID int,
                AUTHOR_ID int,
                PRIMARY KEY (RULE_ID)
                )
                """, raise_on_error=False)

        self.query(f"""
        CREATE TABLE DOMAIN_GAMES
        (
        DOMAIN varchar(100),
        ID int,
        NAME varchar(255),
        MODE int,
        FORMAT int,
        PASSING_SEQUENCE int,
        START_TIME TIMESTAMP_NTZ,
        END_TIME TIMESTAMP_NTZ,
        PLAYER_IDS varchar(500),
        DESCRIPTION_TRUNCATED varchar({MAX_DESCRIPTION_LENGTH + 3}),
        DESCRIPTION_REAL_LENGTH int,
        AUTHORS varchar(250),
        AUTHORS_IDS varchar(250),
        FORUM_THREAD_ID int,
        LAST_MESSAGE_ID int,
        LAST_MESSAGE_TEXT varchar({MAX_LAST_MESSAGE_LENGTH + 3}),
        PRIMARY KEY (DOMAIN, ID)
        )
        """, raise_on_error=False)

        self.query("""
        CREATE TABLE DOMAIN_QUERY_STATUS
        (
        DOMAIN varchar(100),
        LAST_QUERY_TIME TIMESTAMP_NTZ,
        PRIMARY KEY (DOMAIN)
        )
        """, raise_on_error=False)

        self.query(f"""
                CREATE TABLE DOMAIN_GAMES_TEMP
                (
                DOMAIN varchar(100),
                ID int,
                NAME varchar(255),
                MODE int,
                FORMAT int,
                PASSING_SEQUENCE int,
                START_TIME TIMESTAMP_NTZ,
                END_TIME TIMESTAMP_NTZ,
                PLAYER_IDS varchar(500),
                DESCRIPTION_TRUNCATED varchar({MAX_DESCRIPTION_LENGTH + 3}),
                DESCRIPTION_REAL_LENGTH int,
                AUTHORS varchar(250),
                AUTHORS_IDS varchar(250),
                FORUM_THREAD_ID int,
                LAST_MESSAGE_ID int,
                LAST_MESSAGE_TEXT varchar({MAX_LAST_MESSAGE_LENGTH + 3}),
                PRIMARY KEY (DOMAIN, ID)
                )
                """, raise_on_error=False)

        self.query("""
                CREATE TABLE USER_LANGUAGE
                (
                USER_ID varchar(100),
                LANGUAGE int,
                PRIMARY KEY (USER_ID)
                )
                """, raise_on_error=False)

        self.query("""
                CREATE VIEW RULE_DESCRIPTION_V
                AS
                SELECT
                *, 
                CASE 
                WHEN PLAYER_ID IS NULL AND TEAM_ID IS NULL AND GAME_ID IS NULL AND AUTHOR_ID IS NULL
                 THEN 1
                 ELSE 0 
                END as IS_COARSE_RULE
                FROM RULE_DESCRIPTION
                """, raise_on_error=False)

        self.query(f"""CREATE VIEW DOMAIN_GAMES_DIFFERENCES
        AS
        WITH changes_all as (
            SELECT 
            temp.DOMAIN, temp.ID, 
            CASE WHEN ex.DOMAIN IS NULL THEN 1 ELSE 0 END as GAME_NEW,
            CASE WHEN temp.NAME <> ex.NAME THEN 1 ELSE 0 END as NAME_CHANGED,
            ex.NAME as OLD_NAME,
            temp.NAME as NEW_NAME,
            CASE WHEN temp.PASSING_SEQUENCE <> ex.PASSING_SEQUENCE THEN 1 ELSE 0 END as PASSING_SEQUENCE_CHANGED,
            ex.PASSING_SEQUENCE as OLD_PASSING_SEQUENCE,
            temp.PASSING_SEQUENCE as NEW_PASSING_SEQUENCE,
            CASE WHEN temp.START_TIME <> ex.START_TIME THEN 1 ELSE 0 END as START_TIME_CHANGED,
            ex.START_TIME as OLD_START_TIME,
            temp.START_TIME as NEW_START_TIME,
            CASE WHEN temp.END_TIME <> ex.END_TIME THEN 1 ELSE 0 END as END_TIME_CHANGED,
            ex.END_TIME as OLD_END_TIME,
            temp.END_TIME as NEW_END_TIME,
            CASE WHEN IFNULL(temp.PLAYER_IDS, '') <> IFNULL(ex.PLAYER_IDS, '')
             THEN 1 ELSE 0 END as PLAYERS_LIST_CHANGED,
            ex.PLAYER_IDS as OLD_PLAYER_IDS,
            temp.PLAYER_IDS as NEW_PLAYER_IDS,
            CASE WHEN abs(temp.DESCRIPTION_REAL_LENGTH - ex.DESCRIPTION_REAL_LENGTH) * 
            1.0 / (ex.DESCRIPTION_REAL_LENGTH + 1) > {PERCENTAGE_CHANGE_TO_TRIGGER} THEN 1 ELSE 0 END
            as DESCRIPTION_SIGNIFICANTLY_CHANGED,
            ex.DESCRIPTION_TRUNCATED as OLD_DESCRIPTION_TRUNCATED,
            temp.DESCRIPTION_TRUNCATED as NEW_DESCRIPTION_TRUNCATED,
            CASE WHEN IFNULL(temp.DESCRIPTION_TRUNCATED, '') <> IFNULL(ex.DESCRIPTION_TRUNCATED, '') 
            THEN 1 ELSE 0 END as DESCRIPTION_CHANGED,
            CASE WHEN IFNULL(temp.LAST_MESSAGE_ID, '') <> IFNULL(ex.LAST_MESSAGE_ID, '')
            THEN 1 ELSE 0 END as NEW_MESSAGE,
            temp.LAST_MESSAGE_TEXT as NEW_MESSAGE_TEXT,
            temp.AUTHORS as AUTHORS,
            temp.AUTHORS_IDS as AUTHORS_IDS,
            temp.MODE as GAME_MODE,
            temp.FORMAT as GAME_FORMAT,
            temp.FORUM_THREAD_ID as FORUM_THREAD_ID,
            temp.LAST_MESSAGE_ID as NEW_LAST_MESSAGE_ID
            FROM DOMAIN_GAMES_TEMP as temp
            LEFT OUTER JOIN DOMAIN_GAMES as ex
            ON (temp.DOMAIN = ex.DOMAIN AND temp.ID = ex.ID)
        )
        SELECT *
        FROM changes_all
        WHERE GAME_NEW + NAME_CHANGED + PASSING_SEQUENCE_CHANGED + START_TIME_CHANGED + 
        END_TIME_CHANGED + PLAYERS_LIST_CHANGED + DESCRIPTION_SIGNIFICANTLY_CHANGED + 
        DESCRIPTION_CHANGED + NEW_MESSAGE > 0
        """, raise_on_error=False)

        self.query("""
                        CREATE TABLE UPDATE_STATUS
                        (
                        USER_ID int,
                        DOMAIN varchar(100),
                        GAME_ID int,
                        CHANGE varchar(1000),
                        DELIVERED TIMESTAMP_NTZ
                        )
                        """, raise_on_error=False)

        return None

    def query(
            self,
            query_text: str,
            params: typing.Iterable[typing.Any] = None,
            safe: bool = False,
            raise_on_error: bool = True
    ) -> typing.Optional[pd.DataFrame]:
        try:
            if not safe:
                res = pd.read_sql(query_text, self._db_conn, params=params)
            else:
                res = self._db_conn.execute(query_text, params)
        except Exception as e:
            if raise_on_error:
                raise e
            exc_txt = str(e)
            if exc_txt == "'NoneType' object is not iterable":
                return None
            res = pd.DataFrame([{"Exception_text": exc_txt}])
        return res

    def add_rule(self, tg_id: int, rule: Rule) -> bool:
        df = pd.DataFrame([rule.to_json()])
        # res = "Rule added"
        try:
            df.to_sql("RULE_DESCRIPTION", self._db_conn, if_exists="append", index=False)
        except IntegrityError:
            pass
            # res = "Rule already exists"

        df = pd.DataFrame([{
            "USER_ID": tg_id,
            "RULE_ID": rule.rule_id,
            "RULE_ADDED_DATE": datetime.datetime.utcnow(),
        }])
        res = True
        try:
            df.to_sql("USER_SUBSCRIPTION", self._db_conn, if_exists="append", index=False)
        except IntegrityError:
            res = False
        return res

    def add_domain_to_user_outer(self, tg_id: int, domain: str) -> typing.Tuple[bool, Rule]:
        try:
            domain_inst = Domain.from_url(domain)
        except Exception:
            raise InvalidDomainError(domain)
        self.track_domain_outer(domain)
        rule = Rule(domain=domain_inst)
        succ = self.add_rule(tg_id, rule)
        return succ, rule

    def add_mixed_rule_outer(self, tg_id: int, domain: str, **kwargs) -> typing.Tuple[bool, Rule]:
        try:
            domain_inst = Domain.from_url(domain)
        except Exception:
            raise InvalidDomainError(domain)
        self.track_domain_outer(domain)
        rule = Rule(domain=domain_inst, **kwargs)
        succ = self.add_rule(tg_id, rule)
        return succ, rule

    def is_domain_tracked(self, domain: Domain) -> bool:
        domain_normalized_url = domain.full_url
        res = self.query(
            """
            SELECT DOMAIN
            FROM DOMAIN_QUERY_STATUS
            WHERE 1=1
            AND DOMAIN = :domain
            """,
            {"domain": domain_normalized_url}
        )

        if res is None or res.empty:
            return False

        return True

    def track_domain(self, domain: Domain) -> bool:
        domain_normalized_url = domain.full_url
        row = pd.DataFrame([{
            "DOMAIN": domain_normalized_url,
            "LAST_QUERY_TIME": datetime.datetime.utcnow().replace(microsecond=0),
        }])
        res = True
        try:
            row.to_sql("DOMAIN_QUERY_STATUS", self._db_conn, if_exists="append", index=False)
        except IntegrityError:
            res = False

        games = domain.get_games()
        for game in games:
            self.game_to_db(game)

        return res

    def track_domain_outer(self, domain: str) -> None:
        try:
            domain = Domain.from_url(domain)
        except Exception:
            raise InvalidDomainError(domain)
        is_tracked = self.is_domain_tracked(domain)
        if not is_tracked:
            self.track_domain(domain)
        return None

    def get_user_domains(self, tg_id: int) -> typing.List[str]:
        res = self.query(
            """
            SELECT 
            DOMAIN
            FROM USER_SUBSCRIPTION as us
            INNER JOIN RULE_DESCRIPTION as rd
            ON (us.RULE_ID = rd.RULE_ID)
            WHERE USER_ID = :tg_id
            GROUP BY 1
            """,
            {"tg_id": tg_id}
        )

        domains = res["DOMAIN"].tolist()

        return domains

    def get_user_rules(self, tg_id: int) -> typing.List[Rule]:
        res = self.query(
            """
            SELECT 
            rd.*
            FROM USER_SUBSCRIPTION as us
            INNER JOIN RULE_DESCRIPTION as rd
            ON (us.RULE_ID = rd.RULE_ID)
            WHERE USER_ID = :tg_id
            ORDER BY us.RULE_ADDED_DATE
            """,
            {"tg_id": tg_id}
        )
        rules = []
        for _, row in res.iterrows():
            # noinspection PyTypeChecker
            rule = Rule.from_json(row.to_dict())
            rules.append(rule)

        return rules

    def game_to_db(
            self,
            game: EncounterGame,
            table_name: str = "DOMAIN_GAMES",
            if_exists_action: str = 'append',
    ) -> bool:
        row = pd.DataFrame([
            {
                **game.to_json(),
            }
        ])
        res = True
        try:
            row.to_sql(table_name, self._db_conn, if_exists=if_exists_action, index=False)
        except IntegrityError:
            res = False

        return res

    def games_to_db(
            self,
            games: typing.List[EncounterGame],
            table_name: str = "DOMAIN_GAMES",
            if_exists_action: str = 'append',
    ) -> bool:
        row = pd.DataFrame(
            [
                {**game.to_json()}
                for game in games
            ]
        )
        res = True
        if not row.empty:
            try:
                row.to_sql(table_name, self._db_conn, if_exists=if_exists_action, index=False)
            except IntegrityError:
                res = False

        return res

    def show_games(self, domain: Domain) -> typing.List[EncounterGame]:
        res = self.query(
            """
            SELECT * 
            FROM DOMAIN_GAMES
            WHERE DOMAIN = :domain
            ORDER BY START_TIME
            """,
            {"domain": domain.full_url}
        )

        games = [
            EncounterGame.from_json(row)
            for _, row in res.iterrows()
        ]
        return games

    def set_user_language(self, tg_id: int, language: Language) -> None:
        row = pd.DataFrame([
            {"USER_ID": tg_id, "LANGUAGE": language.value},
        ])

        try:
            row.to_sql("USER_LANGUAGE", self._db_conn, if_exists="append", index=False)
        except IntegrityError:
            query = "UPDATE USER_LANGUAGE SET LANGUAGE = :language WHERE USER_ID = :user_id"
            res = self.query(query, {"user_id": tg_id, "language": language.value}, raise_on_error=False)
            assert res is None, res["Exception_text"].iloc[0]
        return None

    def get_user_language(self, tg_id: int) -> Language:
        query = "SELECT LANGUAGE FROM USER_LANGUAGE WHERE USER_ID = :user_id"
        res = self.query(query, {"user_id": tg_id})
        if res.empty:
            lang = Language.English
            self.set_user_language(tg_id, lang)
        else:
            lang = res["LANGUAGE"].iloc[0]
            lang = Language(lang)

        return lang

    def show_games_multiple_domains(self, domains: typing.List[Domain]) -> typing.List[EncounterGame]:
        domains_tuple = tuple(domain.full_url for domain in domains)
        res = self.query(
            f"""
            SELECT * 
            FROM DOMAIN_GAMES
            WHERE DOMAIN IN {domains_tuple}
            ORDER BY START_TIME
            """,
        )

        games = [
            EncounterGame.from_json(row)
            for _, row in res.iterrows()
        ]
        return games

    def get_all_user_games(self, tg_id: int, n_days_in_future: int = None) -> typing.List[EncounterGame]:
        query = f"""
        with user_rules as (
            SELECT
            RULE_ID
            FROM USER_SUBSCRIPTION
            WHERE USER_ID = :user_id
        ),
        rules_desc as (
            SELECT 
            rd.*
            FROM user_rules as ur
            INNER JOIN RULE_DESCRIPTION_V as rd
            USING (RULE_ID)
        ),
        games_matched as (
            SELECT 
            dg.*,
            ROW_NUMBER() OVER (PARTITION BY dg.DOMAIN, dg.ID ORDER BY RANDOM()) as rn
            FROM rules_desc as rd
            INNER JOIN DOMAIN_GAMES as dg
            ON 
            (
                1=0
                OR (
                    1=1
                    AND rd.IS_COARSE_RULE = 1
                    AND rd.DOMAIN = dg.DOMAIN
                )
                OR (
                    1=1
                    AND rd.IS_COARSE_RULE = 0
                    AND rd.DOMAIN = dg.DOMAIN
                    AND (
                        1=0
                        OR IFNULL(rd.GAME_ID, -1) = dg.ID
                        OR (
                            dg.FORMAT = {GameFormat.Single.value}
                            AND
                            dg.PLAYER_IDS LIKE '%' || IFNULL(rd.PLAYER_ID, -1) || '%'
                        )
                        OR (
                            dg.FORMAT = {GameFormat.Team.value}
                            AND
                            dg.PLAYER_IDS LIKE '%' || IFNULL(rd.TEAM_ID, -1) || '%'
                        )
                    )
                )
            )
        )
        SELECT *
        FROM games_matched
        WHERE 1=1
        AND rn = 1
        AND START_TIME <= :end_date
        ORDER BY START_TIME
        """
        if n_days_in_future is None:
            end_date = datetime.datetime(2100, 1,  1)
        else:
            end_date = datetime.datetime.utcnow() + datetime.timedelta(days=n_days_in_future)

        res = self.query(query, {"user_id": tg_id, "end_date": end_date})
        games = [
            EncounterGame.from_json(row)
            for _, row in res.iterrows()
        ]
        return games

    def show_games_outer(self, tg_id: int, domain: str) -> typing.List[EncounterGame]:
        if domain == "All":
            domains = self.get_user_domains(tg_id)
            domains_instances = [
                Domain.from_url(domain)
                for domain in domains
            ]
            games = self.show_games_multiple_domains(domains_instances)
        else:
            domain_inst = Domain.from_url(domain)
            games = self.show_games(domain_inst)

        return games

    def games_to_temp_table(
            self,
            games: typing.List[EncounterGame],
    ) -> None:
        self.games_to_db(games, "DOMAIN_GAMES_TEMP", "replace")
        return None

    def commit_update(self) -> None:
        self.merge_into_truth_db()
        self.set_update_time()
        return None

    def merge_into_truth_db(self) -> None:
        delete_query = f"""
        DELETE FROM DOMAIN_GAMES
        WHERE 1=1
        AND DOMAIN IN (select DISTINCT DOMAIN FROM DOMAIN_GAMES_TEMP)
        """
        self.query(delete_query, raise_on_error=False)
        insert_query = """
        INSERT INTO DOMAIN_GAMES
        SELECT * FROM DOMAIN_GAMES_TEMP
        """
        self.query(insert_query, raise_on_error=False)
        return None

    def set_update_time(self) -> None:
        query = f"""
        UPDATE DOMAIN_QUERY_STATUS
        SET LAST_QUERY_TIME = CURRENT_TIMESTAMP
        WHERE 1=1
        AND DOMAIN IN (SELECT DISTINCT DOMAIN FROM DOMAIN_GAMES_TEMP)
        """
        res = self.query(query, raise_on_error=False)
        assert res is None, res["Exception_text"].iloc[0]
        return None

    def find_domains_due(self, delta: int) -> typing.List[Domain]:
        query = """
        SELECT DOMAIN
        FROM DOMAIN_QUERY_STATUS
        WHERE 1=1
        AND (julianday(CURRENT_TIMESTAMP) - julianday(LAST_QUERY_TIME)) * 86400.0 > :delta
        """
        res = self.query(query, {"delta": delta}, raise_on_error=False)
        domains = res["DOMAIN"].tolist()
        domains = [Domain.from_url(d) for d in domains]
        return domains

    def users_to_notify(self) -> pd.DataFrame:
        query = f"""
        WITH rules_triggered as (
            SELECT
            us.RULE_ID,
            dd.*,
            ROW_NUMBER() OVER (PARTITION BY dd.DOMAIN, dd.ID, us.RULE_ID ORDER BY RANDOM()) as rn
            FROM DOMAIN_GAMES_DIFFERENCES as dd
            INNER JOIN RULE_DESCRIPTION_V as us
            ON 
            (
                (
                    1=1
                    AND us.DOMAIN = dd.DOMAIN
                    AND (
                        1=0
                        OR dd.GAME_NEW = 1
                        OR dd.NAME_CHANGED = 1
                        OR dd.PASSING_SEQUEN`CE_CHANGED = 1
                        OR (julianday(NEW_START_TIME) - julianday(OLD_START_TIME)) * 24 > {MIN_HOURS_GAME_CHANGE_NOTIFY}
                        OR dd.DESCRIPTION_SIGNIFICANTLY_CHANGED = 1
                    )
                    AND us.IS_COARSE_RULE = 1
                )
                OR 
                (
                    1=1
                    AND dd.GAME_FORMAT = {GameFormat.Single.value}
                    AND dd.NEW_PLAYER_IDS LIKE '%' || us.PLAYER_ID || '%'
                    AND dd.DOMAIN = us.DOMAIN
                    AND us.IS_COARSE_RULE = 0
                    AND (
                        dd.PLAYERS_LIST_CHANGED - 
                        (
                            dd.GAME_NEW + dd.NAME_CHANGED + dd.PASSING_SEQUENCE_CHANGED + dd.START_TIME_CHANGED +
                            dd.END_TIME_CHANGED + dd.DESCRIPTION_SIGNIFICANTLY_CHANGED + dd.DESCRIPTION_CHANGED + 
                            dd.NEW_MESSAGE
                        )
                        != 1
                    )
                )
                OR
                (
                    1=1
                    AND dd.GAME_FORMAT = {GameFormat.Team.value}
                    AND dd.NEW_PLAYER_IDS LIKE '%' || us.TEAM_ID || '%'
                    AND dd.DOMAIN = us.DOMAIN
                    AND us.IS_COARSE_RULE = 0
                    AND (
                        dd.PLAYERS_LIST_CHANGED - 
                        (
                            dd.GAME_NEW + dd.NAME_CHANGED + dd.PASSING_SEQUENCE_CHANGED + dd.START_TIME_CHANGED +
                            dd.END_TIME_CHANGED + dd.DESCRIPTION_SIGNIFICANTLY_CHANGED + dd.DESCRIPTION_CHANGED + 
                            dd.NEW_MESSAGE
                        )
                        != 1
                    )
                )
                OR 
                (
                    1=1
                    AND dd.AUTHORS_IDS LIKE '%' || us.AUTHOR_ID || '%'
                    AND dd.DOMAIN = us.DOMAIN
                    AND us.IS_COARSE_RULE = 0
                )
                OR 
                (
                    1=1
                    AND dd.DOMAIN = us.DOMAIN
                    AND dd.ID = us.GAME_ID
                    AND us.IS_COARSE_RULE = 0
                )
            )
        ),
        unique_rules_triggered as (
            SELECT *
            FROM rules_triggered
            WHERE 1=1
            AND rn = 1
        ),
        users_triggered_rules as (
            SELECT 
            rt.*, us.USER_ID, 
            ROW_NUMBER() OVER (PARTITION BY us.USER_ID, rt.DOMAIN, rt.ID ORDER BY RANDOM()) as rn_outer
            FROM unique_rules_triggered as rt
            INNER JOIN USER_SUBSCRIPTION as us
            ON (rt.RULE_ID = us.RULE_ID)
        ),
        one_row_per_user_update as (
            SELECT *
            FROM users_triggered_rules
            WHERE rn_outer = 1
        )
        SELECT a.*, b.LANGUAGE
        FROM one_row_per_user_update as a
        INNER JOIN USER_LANGUAGE as b
        ON (a.USER_ID = b.USER_ID)
        """
        users_to_notify_df = self.query(query)

        return users_to_notify_df

    def is_user_within_rule_limits(self, tg_id: int) -> bool:
        query = """
        SELECT COUNT(*) as N_RULES
        FROM USER_SUBSCRIPTION
        WHERE 1=1
        AND USER_ID = :user_id
        """
        cnt_rules = self.query(query, {"user_id": tg_id})
        n_rules = cnt_rules["N_RULES"].iloc[0]
        is_ok = n_rules <= MAX_USER_RULES_ALLOWED
        return is_ok

    def get_user_rule_by_id(self, tg_id: int, rule_id: str) -> typing.Optional[Rule]:
        query = """
        SELECT *
        FROM USER_SUBSCRIPTION 
        INNER JOIN RULE_DESCRIPTION
        USING (RULE_ID)
        WHERE 1=1
        AND USER_ID = :user_id
        AND RULE_ID = :rule_id
        """
        rule_df = self.query(
            query, {
                "user_id": tg_id,
                "rule_id": rule_id,
            },
            raise_on_error=False
        )
        if rule_df is not None and "Exception_text" not in rule_df.columns:
            res = Rule.from_json(rule_df.iloc[0].to_dict())
        else:
            res = None

        return res

    def get_updates(
            self: EncounterNewsDB,
            domains_due_override: typing.List[Domain] = None,
    ) -> typing.List[Update]:
        if domains_due_override:
            domains_due = domains_due_override
        else:
            domains_due = self.find_domains_due(UPDATE_FREQUENCY_SECONDS)

        if domains_due:
            new_games = []

            for domain in domains_due:
                new_games_pt = domain.get_games()
                new_games.extend(new_games_pt)

            self.games_to_temp_table(new_games)
            users_to_notify = self.users_to_notify()
        else:
            users_to_notify = pd.DataFrame()

        # noinspection PyTypeChecker
        notifs = [
            Update.from_row(row)
            for _, row in users_to_notify.iterrows()
        ]

        return notifs

    def updates_to_db(self, updates: typing.List[Update]) -> None:
        df = pd.DataFrame(
            [
                u.to_json()
                for u in updates
            ]
        )
        df.to_sql("UPDATE_STATUS", self._db_conn, if_exists="append", index=False)
        return None

    def delete_user_rule_by_id(self, tg_id: int, rule_id: str) -> None:
        query = """
        DELETE FROM USER_SUBSCRIPTION 
        WHERE 1=1
        AND USER_ID = :user_id
        AND RULE_ID = :rule_id
        """
        res = self.query(
            query, {
                "user_id": tg_id,
                "rule_id": rule_id,
            },
            raise_on_error=False
        )

        assert res is None, res["Exception_text"].iloc[0]
        return res

    def prune_rule_descriptions(self) -> None:
        query = """
        WITH UNUSED_RULES as (
            SELECT 
            rd.RULE_ID
            FROM RULE_DESCRIPTION as rd
            LEFT JOIN USER_SUBSCRIPTION as us
            ON (rd.RULE_ID = us.RULE_ID)
            WHERE 1=1
            AND us.RULE_ID IS NULL
            GROUP BY 1
        )
        DELETE FROM RULE_DESCRIPTION 
        WHERE 1=1
        AND RULE_ID IN UNUSED_RULES
        """
        res = self.query(
            query,
            raise_on_error=False
        )

        assert res is None, res["Exception_text"].iloc[0]
        return res

    def prune_domain_query_status(self) -> None:
        query = """
        WITH UNUSED_DOMAINS as (
            SELECT 
            dqs.DOMAIN
            FROM DOMAIN_QUERY_STATUS as dqs
            LEFT JOIN RULE_DESCRIPTION as rd
            ON (dqs.DOMAIN = rd.DOMAIN)
            WHERE 1=1
            AND rd.DOMAIN IS NULL
            GROUP BY 1
        )
        DELETE FROM DOMAIN_QUERY_STATUS 
        WHERE 1=1
        AND DOMAIN IN UNUSED_DOMAINS
        """
        res = self.query(
            query,
            raise_on_error=False
        )

        assert res is None, res["Exception_text"].iloc[0]
        return res

    def close_connection(self) -> None:
        # noinspection PyBroadException
        try:
            self.query("COMMIT", safe=False)
        except Exception:
            pass
        self._db_conn.close()
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close_connection()
        return None


if __name__ == '__main__':

    from constants import DB_LOCATION
    with EncounterNewsDB(DB_LOCATION) as db_:
        d_ = Domain("kharkiv")
        db_.get_updates(domains_due_override=[d_])
        db_.commit_update()
