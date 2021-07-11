"""
DB API for the bot
"""

from sqlite3 import connect, Connection
from dataclasses import dataclass, field
import typing
import os
import datetime
from sqlite3 import IntegrityError

import pandas as pd

from meta import Domain, EncounterGame, Rule, GameFormat, Language
from constants import PERCENTAGE_CHANGE_TO_TRIGGER, MAX_DESCRIPTION_LENGTH

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
                PRIMARY KEY (DOMAIN, ID)
                )
                """, raise_on_error=False)

        self.query(f"""
                CREATE TABLE DOMAIN_GAMES_DIFFERENCES
                (
                DOMAIN varchar(100),
                ID int,
                GAME_NEW int,
                NAME_CHANGED int,
                OLD_NAME varchar(255),
                NEW_NAME varchar(255),
                PASSING_SEQUENCE_CHANGED int,
                OLD_PASSING_SEQUENCE int,
                NEW_PASSING_SEQUENCE int,
                START_TIME_CHANGED int,
                OLD_START_TIME TIMESTAMP_NTZ,
                NEW_START_TIME TIMESTAMP_NTZ,
                END_TIME_CHANGED int,
                OLD_END_TIME TIMESTAMP_NTZ,
                NEW_END_TIME TIMESTAMP_NTZ,
                PLAYERS_LIST_CHANGED int,
                OLD_PLAYER_IDS varchar(500),
                NEW_PLAYER_IDS varchar(500),
                DESCRIPTION_SIGNIFICANTLY_CHANGED int,
                OLD_DESCRIPTION_TRUNCATED varchar({MAX_DESCRIPTION_LENGTH + 3}),
                NEW_DESCRIPTION_TRUNCATED varchar({MAX_DESCRIPTION_LENGTH + 3}),
                DESCRIPTION_CHANGED int,
                MODE int,
                FORMAT int,
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

    def add_rule(self, tg_id: int, rule: Rule):
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
        }])
        res = "User rule added"
        try:
            df.to_sql("USER_SUBSCRIPTION", self._db_conn, if_exists="append", index=False)
        except IntegrityError:
            res = "You already have this rule"
        return res

    def add_domain_to_user_outer(self, tg_id: int, domain: str) -> str:
        domain_inst = Domain.from_url(domain)
        self.track_domain(domain_inst)
        rule = Rule(domain=domain_inst)
        res = self.add_rule(tg_id, rule)
        return res

    def add_mixed_rule_outer(self, tg_id: int, domain: str, **kwargs) -> str:
        domain_inst = Domain.from_url(domain)
        rule = Rule(domain=domain_inst, **kwargs)
        res = self.add_rule(tg_id, rule)
        return res

    # def add_domain_to_user(self, tg_id: int, domain: Domain) -> str:
    #
    #     domain_normalized_url = domain.full_url
    #     row = pd.DataFrame([{
    #         "USER_ID": tg_id,
    #         "DOMAIN": domain_normalized_url,
    #     }])
    #     res = "Domain added to the list"
    #     try:
    #         row.to_sql("USER_SUBSCRIPTION", self._db_conn, if_exists="append", index=False)
    #     except IntegrityError:
    #         res = "You already have the domain in the watched list"
    #     return res

    def is_domain_tracked(self, domain: Domain, language: Language) -> bool:
        domain_normalized_url = domain.full_url
        res = self.query(
            """
            SELECT DOMAIN
            FROM DOMAIN_QUERY_STATUS
            WHERE 1=1
            AND DOMAIN = :domain
            AND LANGUAGE = :language
            """,
            {"domain": domain_normalized_url, "language": language}
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

    def get_user_domains(self, tg_id: int) -> typing.List[str]:
        res = self.query(
            """
            SELECT DOMAIN
            FROM USER_SUBSCRIPTION as us
            INNER JOIN RULE_DESCRIPTION as rd
            ON (us.RULE_ID = rd.RULE_ID)
            WHERE USER_ID = :tg_id
            """,
            {"tg_id": tg_id}
        )

        domains = res["DOMAIN"].tolist()

        return domains

    def get_user_rules(self, tg_id: int) -> typing.List[Rule]:
        res = self.query(
            """
            SELECT rd.*
            FROM USER_SUBSCRIPTION as us
            INNER JOIN RULE_DESCRIPTION as rd
            ON (us.RULE_ID = rd.RULE_ID)
            WHERE USER_ID = :tg_id
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
            res = self.query(query, {"user_id": tg_id, "language": language}, raise_on_error=False)
            assert res is None, res["Expcetion_text"].iloc[0]
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

    def update_domains(self, domains: typing.List[Domain]) -> None:
        new_games = []

        for domain in domains:
            new_games_pt = domain.get_games()
            new_games.extend(new_games_pt)

        self.games_to_db(new_games, "DOMAIN_GAMES_TEMP", "replace")
        self.find_difference()
        self.merge_into_truth_db(domains)
        self.set_update_time(domains)
        return None

    def merge_into_truth_db(self, domains: typing.List[Domain]) -> None:
        domains_tuple = tuple(d.full_url for d in domains)
        if len(domains_tuple) == 1:
            domains_tuple = f"({domains_tuple[0]})"
        delete_query = f"""
        DELETE FROM DOMAIN_GAMES
        WHERE 1=1
        AND DOMAIN IN {domains_tuple}
        """
        self.query(delete_query, raise_on_error=False)
        insert_query = """
        INSERT INTO DOMAIN_GAMES
        SELECT * FROM DOMAIN_GAMES_TEMP
        """
        self.query(insert_query, raise_on_error=False)
        return None

    def set_update_time(self, domains: typing.List[Domain]) -> None:
        domains_tuple = tuple(d.full_url for d in domains)
        if len(domains_tuple) == 1:
            domains_tuple = f"({domains_tuple[0]})"
        query = f"""
        UPDATE DOMAIN_QUERY_STATUS
        SET LAST_QUERY_TIME = CURRENT_TIMESTAMP
        WHERE 1=1
        AND DOMAIN IN {domains_tuple}
        """
        res = self.query(query,  raise_on_error=False)
        assert res is None, res["Exception_text"].iloc[0]
        return None

    def find_difference(self) -> None:
        drop_query = """DROP TABLE IF EXISTS DOMAIN_GAMES_DIFFERENCES"""
        self.query(drop_query, raise_on_error=False)

        create_query = f"""
        CREATE TABLE DOMAIN_GAMES_DIFFERENCES
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
            CASE WHEN temp.PLAYER_IDS <> ex.PLAYER_IDS THEN 1 ELSE 0 END as PLAYERS_LIST_CHANGED,
            ex.PLAYER_IDS as OLD_PLAYER_IDS,
            temp.PLAYER_IDS as NEW_PLAYER_IDS,
            CASE WHEN abs(temp.DESCRIPTION_REAL_LENGTH - ex.DESCRIPTION_REAL_LENGTH) * 
            1.0 / (ex.DESCRIPTION_REAL_LENGTH + 1) > {PERCENTAGE_CHANGE_TO_TRIGGER} THEN 1 ELSE 0 END
            as DESCRIPTION_SIGNIFICANTLY_CHANGED,
            ex.DESCRIPTION_TRUNCATED as OLD_DESCRIPTION_TRUNCATED,
            temp.DESCRIPTION_TRUNCATED as NEW_DESCRIPTION_TRUNCATED,
            CASE WHEN temp.DESCRIPTION_TRUNCATED <> ex.DESCRIPTION_TRUNCATED THEN 1 ELSE 0 END as DESCRIPTION_CHANGED,
            temp.MODE as GAME_MODE,
            temp.FORMAT as GAME_FORMAT
            FROM DOMAIN_GAMES_TEMP as temp
            LEFT OUTER JOIN DOMAIN_GAMES as ex
            ON (temp.DOMAIN = ex.DOMAIN AND temp.ID = ex.ID)
        )
        SELECT *
        FROM changes_all
        WHERE GAME_NEW + NAME_CHANGED + PASSING_SEQUENCE_CHANGED + START_TIME_CHANGED + 
        END_TIME_CHANGED + PLAYERS_LIST_CHANGED + DESCRIPTION_SIGNIFICANTLY_CHANGED + DESCRIPTION_CHANGED > 0
        """
        res = self.query(create_query, raise_on_error=False)

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
            INNER JOIN RULE_DESCRIPTION as us
            ON 
            (
                (
                    1=1
                    AND us.DOMAIN = dd.DOMAIN
                    AND (
                        1=0
                        OR dd.GAME_NEW = 1
                        OR dd.NAME_CHANGED = 1
                        OR dd.PASSING_SEQUENCE_CHANGED = 1
                        OR dd.START_TIME_CHANGED = 1
                        OR dd.DESCRIPTION_SIGNIFICANTLY_CHANGED = 1
                    )
                )
                OR 
                (
                    1=1
                    AND dd.GAME_FORMAT = {GameFormat.Single.value}
                    AND dd.NEW_PLAYER_IDS LIKE '%' || us.PLAYER_ID || '%'
                    AND dd.DOMAIN = us.DOMAIN
                )
                OR
                (
                    1=1
                    AND dd.GAME_FORMAT = {GameFormat.Team.value}
                    AND dd.NEW_PLAYER_IDS LIKE '%' || us.TEAM_ID || '%'
                    AND dd.DOMAIN = us.DOMAIN
                )
                OR 
                (
                    1=1
                    AND dd.DOMAIN = us.DOMAIN
                    AND dd.ID = us.GAME_ID
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
    with EncounterNewsDB(DB_LOCATION) as db:
        d_ = Domain("kharkiv")
        db.update_domains([d_])
