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
            self._db_conn.close()
            self._db_conn = connect(self.db_location)
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

    def game_to_db(self, game: EncounterGame) -> bool:
        row = pd.DataFrame([
            {
                **game.to_json(),
            }
        ])
        res = True
        try:
            row.to_sql("DOMAIN_GAMES", self._db_conn, if_exists="append", index=False)
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
