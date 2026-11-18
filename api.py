import os
import sqlite3
import time
from collections import deque
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

import banco
import regras
from relogio import Relogio

DEMO = os.environ.get("MODO_DEMO") == "1"
PIN = os.environ.get("PIN_PROFESSOR", "1234")
NOMES_DEMO = ["Ana", "Bruno", "Carla", "Diego", "Elisa"]

banco.iniciar()


def semear():
    for i, nome in enumerate(NOMES_DEMO, start=1):
        regras.cadastrar_aluno(i, nome)


if DEMO and not regras.listar_alunos():
    semear()

relogio = Relogio(max(time.time(), regras.ultimo_instante()))
eventos = deque(maxlen=12)


def registrar(texto, cls=""):
    hora = time.strftime("%H:%M:%S", time.localtime(relogio.agora()))
    eventos.appendleft({"hora": hora, "texto": texto, "cls": cls})


def exigir_pin(pin):
    if pin != PIN:
        raise HTTPException(403, "PIN do professor incorreto.")


def exigir_demo():
    if not DEMO:
        raise HTTPException(404, "Disponível apenas no modo simulação.")


app = FastAPI(title="Controle de saída da sala")


PASTA = Path(__file__).parent


def achar_pagina():
    for caminho in (PASTA / "static" / "index.html", PASTA / "index.html"):
        if caminho.is_file():
            return caminho
    return None


@app.get("/")
def pagina():
    caminho = achar_pagina()
    if caminho is None:
        return HTMLResponse(
            "<h2>Arquivo da página não encontrado</h2>"
            "<p>Crie a pasta <b>static</b> ao lado de <b>api.py</b> e coloque nela o arquivo "
            f"<b>index.html</b>.</p><p>Procurei em: <code>{PASTA / 'static' / 'index.html'}</code></p>",
            status_code=500,
        )
    return FileResponse(caminho)


@app.get("/api/estado")
def estado():
    return {
        "agora": relogio.agora(),
        "velocidade": relogio.vel,
        "limite": regras.LIMITE_SEGUNDOS,
        "max": regras.LIMITE_ESTOUROS,
        "demo": DEMO,
        "alunos": [
            {"id": r["id"], "nome": r["nome"], "estouros": r["estouros"],
             "liberado": bool(r["liberado"]), "saida": r["saida"]}
            for r in regras.estado_alunos()
        ],
        "eventos": list(eventos),
    }


@app.post("/api/digital/{aluno_id}")
def digital(aluno_id: int):
    """Equivale a encostar o dedo no sensor da porta."""
    status, msg = regras.passar_digital(aluno_id, relogio.agora())
    ruim = status in ("negado", "desconhecido") or "passou de" in msg
    registrar(msg, "bad" if ruim else ("ok" if status == "retorno" else ""))
    return {"status": status, "mensagem": msg}


@app.post("/api/professor/liberar/{aluno_id}")
def liberar(aluno_id: int, x_pin: str = Header(default="")):
    exigir_pin(x_pin)
    regras.liberar_aluno(aluno_id)
    registrar(f"Professor liberou uma saída (ID {aluno_id}).", "ok")
    return {"ok": True}


@app.post("/api/professor/zerar/{aluno_id}")
def zerar(aluno_id: int, x_pin: str = Header(default="")):
    exigir_pin(x_pin)
    regras.zerar_contador(aluno_id)
    registrar(f"Professor zerou o contador (ID {aluno_id}).", "ok")
    return {"ok": True}


class NovoAluno(BaseModel):
    id: int
    nome: str


@app.post("/api/alunos")
def cadastrar(aluno: NovoAluno):
    try:
        regras.cadastrar_aluno(aluno.id, aluno.nome.strip())
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Já existe um aluno com esse ID.")
    return {"ok": True}


# ---------- somente no modo simulação ----------
class Velocidade(BaseModel):
    valor: float


class Avanco(BaseModel):
    segundos: float


@app.post("/api/demo/velocidade")
def velocidade(v: Velocidade):
    exigir_demo()
    if not 1 <= v.valor <= 60:
        raise HTTPException(422, "A velocidade deve ficar entre 1 e 60.")
    relogio.definir_velocidade(v.valor)
    return {"ok": True}


@app.post("/api/demo/avancar")
def avancar(a: Avanco):
    exigir_demo()
    relogio.avancar(max(0, min(a.segundos, 3600)))
    return {"ok": True}


@app.post("/api/demo/reiniciar")
def reiniciar():
    exigir_demo()
    regras.resetar_banco()
    semear()
    relogio.reiniciar()
    eventos.clear()
    registrar("Simulação reiniciada. Todos os alunos estão na sala.")
    return {"ok": True}