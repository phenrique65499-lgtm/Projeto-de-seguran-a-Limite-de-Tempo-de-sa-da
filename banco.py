import os
import sqlite3
from pathlib import Path

CAMINHO_DB = Path(os.environ.get("ESCOLA_DB", Path(__file__).parent / "escola.db"))


def conectar():
    con = sqlite3.connect(CAMINHO_DB)
    con.row_factory = sqlite3.Row
    return con


def iniciar():
    with conectar() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS alunos (
                id        INTEGER PRIMARY KEY,   -- mesmo ID gravado no sensor de digital
                nome      TEXT NOT NULL,
                estouros  INTEGER NOT NULL DEFAULT 0,
                liberado  INTEGER NOT NULL DEFAULT 0  -- 1 = professor autorizou uma saída
            );

            CREATE TABLE IF NOT EXISTS saidas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id  INTEGER NOT NULL REFERENCES alunos(id),
                saida     REAL NOT NULL,          -- timestamp (segundos)
                retorno   REAL,                   -- NULL = ainda fora da sala
                estourou  INTEGER NOT NULL DEFAULT 0
            );
            """
        )