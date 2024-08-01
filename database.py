from dataclasses import dataclass
import sqlite3


@dataclass
class Account:
    id: int
    name: str
    auth_key: str
    tg_id: int


class Database:
    def __init__(self, db_path: str) -> None:
        self.connection = sqlite3.Connection(db_path)
        self.cursor = sqlite3.Cursor(self.connection)
        self.setup()
    
    def __del__(self):
        self.connection.close()

    def setup(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                auth_key VARCHAR(150) UNIQUE NOT NULL,
                tg_id INTEGER UNIQUE NOT NULL
            );
            """
        )
        self.connection.commit()

    def add_account(self, name: str, auth_key: str, tg_id: int) -> Account:
        self.cursor.execute(
            """
            INSERT INTO accounts (name, auth_key, tg_id)
            VALUES (?, ?, ?);
            """,
            (name, auth_key, tg_id)
        )
        self.connection.commit()
        return Account(id=self.cursor.lastrowid, name=name, auth_key=auth_key, tg_id=tg_id)
    
    def get_accounts(self) -> list[Account]:
        accounts = self.cursor.execute(
            """
            SELECT id, name, auth_key, tg_id FROM accounts ORDER BY id;
            """
        )
        return [Account(*account) for account in accounts.fetchall()]

    def remove_account(self, id: int):
        self.cursor.execute(
            """
            DELETE FROM accounts WHERE id = ?;
            """,
            (id,)
        )
        self.connection.commit()
