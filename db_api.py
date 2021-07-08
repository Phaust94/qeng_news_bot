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

from meta import Domain, EncounterGame

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
        DOMAIN varchar(100),
        PRIMARY KEY (USER_ID, DOMAIN)
        )
        """, raise_on_error=False)

        self.query("""
        CREATE TABLE DOMAIN_GAMES
        (
        DOMAIN varchar(100),
        ID int,
        NAME varchar(255),
        MODE varchar(255),
        FORMAT varchar(255),
        PASSING_SEQUENCE varchar(255),
        START_TIME TIMESTAMP_NTZ,
        END_TIME TIMESTAMP_NTZ,
        PLAYER_IDS varchar(500),
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

        self.query("""
                CREATE TABLE DOMAIN_GAMES_TEMP
                (
                DOMAIN varchar(100),
                ID int,
                NAME varchar(255),
                MODE varchar(255),
                FORMAT varchar(255),
                PASSING_SEQUENCE varchar(255),
                START_TIME TIMESTAMP_NTZ,
                END_TIME TIMESTAMP_NTZ,
                PLAYER_IDS varchar(500),
                PRIMARY KEY (DOMAIN, ID)
                )
                """, raise_on_error=False)

        self.query("""
                CREATE TABLE DOMAIN_GAMES_DIFFERENCES
                (
                DOMAIN varchar(100),
                ID int,
                GAME_NEW int,
                NAME_CHANGED int,
                FORMAT_CHANGED int,
                PASSING_SEQUENCE_CHANGED int,
                START_TIME_CHANGED int,
                END_TIME_CHANGED int,
                PLAYERS_LIST_CHANGED int,
                PRIMARY KEY (DOMAIN, ID)
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

    def add_domain_to_user_outer(self, tg_id: int, domain: str) -> str:
        domain_inst = Domain.from_url(domain)
        is_tracked = self.is_domain_tracked(domain_inst)
        res = self.add_domain_to_user(tg_id, domain_inst)
        if not is_tracked:
            self.track_domain(domain_inst)
        return res

    def add_domain_to_user(self, tg_id: int, domain: Domain) -> str:

        domain_normalized_url = domain.full_url
        row = pd.DataFrame([{
            "USER_ID": tg_id,
            "DOMAIN": domain_normalized_url,
        }])
        res = "Domain added to the list"
        try:
            row.to_sql("USER_SUBSCRIPTION", self._db_conn, if_exists="append", index=False)
        except IntegrityError:
            res = "You already have the domain in the watched list"
        return res

    def is_domain_tracked(self, domain: Domain) -> bool:
        domain_normalized_url = domain.full_url
        res = self.query(
            """
            SELECT DOMAIN
            FROM DOMAIN_QUERY_STATUS
            WHERE DOMAIN = :domain
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

    def get_user_domains(self, tg_id: int) -> typing.List[str]:
        res = self.query(
            """
            SELECT DOMAIN
            FROM USER_SUBSCRIPTION
            WHERE USER_ID = :tg_id
            """,
            {"tg_id": tg_id}
        )

        domains = res["DOMAIN"].tolist()

        return domains

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
        # TODO: NOTIFY USERS about updates
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

        create_query = """
        CREATE TABLE DOMAIN_GAMES_DIFFERENCES
        AS
        WITH changes_all as (
            SELECT 
            temp.DOMAIN, temp.ID, 
            CASE WHEN ex.DOMAIN IS NULL THEN 1 ELSE 0 END as GAME_NEW,
            CASE WHEN temp.NAME <> ex.NAME THEN 1 ELSE 0 END as NAME_CHANGED,
            CASE WHEN temp.FORMAT <> ex.FORMAT THEN  1 ELSE 0 END as FORMAT_CHANGED,
            CASE WHEN temp.PASSING_SEQUENCE <> ex.PASSING_SEQUENCE THEN 1 ELSE 0 END as PASSING_SEQUENCE_CHANGED,
            CASE WHEN temp.START_TIME <> ex.START_TIME THEN 1 ELSE 0 END as START_TIME_CHANGED,
            CASE WHEN temp.END_TIME <> ex.END_TIME THEN 1 ELSE 0 END as END_TIME_CHANGED,
            CASE WHEN temp.PLAYER_IDS <> ex.PLAYER_IDS THEN 1 ELSE 0 END as PLAYERS_LIST_CHANGED
            FROM DOMAIN_GAMES_TEMP as temp
            LEFT OUTER JOIN DOMAIN_GAMES as ex
            ON (temp.DOMAIN = ex.DOMAIN AND temp.ID = ex.ID)
        )
        SELECT *
        FROM changes_all
        WHERE GAME_NEW + NAME_CHANGED + FORMAT_CHANGED + PASSING_SEQUENCE_CHANGED + START_TIME_CHANGED + END_TIME_CHANGED + PLAYERS_LIST_CHANGED > 0
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
        db.update_domain(d_)
