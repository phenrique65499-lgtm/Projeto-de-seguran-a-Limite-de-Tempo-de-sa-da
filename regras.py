import time

from banco import conectar

LIMITE_SEGUNDOS = 180   # 3 minutos fora da sala
LIMITE_ESTOUROS = 3     # 3 estouros = "Aluno problema"


def fmt(segundos):
    segundos = int(abs(segundos))
    return f"{segundos // 60:02d}:{segundos % 60:02d}"


# ---------- cadastro ----------
def cadastrar_aluno(aluno_id, nome):
    with conectar() as c:
        c.execute("INSERT INTO alunos (id, nome) VALUES (?, ?)", (aluno_id, nome))


def listar_alunos():
    with conectar() as c:
        return c.execute("SELECT * FROM alunos ORDER BY nome").fetchall()


# ---------- digital na porta ----------
def passar_digital(aluno_id, agora=None):
    """Chamada toda vez que o sensor lê uma digital.
    Retorna (status, mensagem). Status: saida | retorno | negado | desconhecido
    """
    agora = agora or time.time()
    with conectar() as c:
        aluno = c.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,)).fetchone()
        if aluno is None:
            return "desconhecido", "Digital não reconhecida."

        aberta = c.execute(
            "SELECT * FROM saidas WHERE aluno_id = ? AND retorno IS NULL", (aluno_id,)
        ).fetchone()

        # --- está fora: é o retorno, o cronômetro para ---
        if aberta:
            duracao = agora - aberta["saida"]
            estourou = duracao > LIMITE_SEGUNDOS
            c.execute(
                "UPDATE saidas SET retorno = ?, estourou = ? WHERE id = ?",
                (agora, int(estourou), aberta["id"]),
            )
            if estourou:
                c.execute("UPDATE alunos SET estouros = estouros + 1 WHERE id = ?", (aluno_id,))
                total = aluno["estouros"] + 1
                msg = (f"{aluno['nome']} voltou após {fmt(duracao)} (passou de 03:00). "
                       f"Estouros: {total}/{LIMITE_ESTOUROS}")
                if total >= LIMITE_ESTOUROS:
                    msg += "  >>> ALUNO PROBLEMA <<<"
            else:
                msg = f"{aluno['nome']} voltou em {fmt(duracao)}. Dentro do tempo."
            return "retorno", msg

        # --- está dentro: tentativa de sair ---
        if aluno["estouros"] >= LIMITE_ESTOUROS and not aluno["liberado"]:
            return "negado", (f"SAÍDA NEGADA: {aluno['nome']} é Aluno problema. "
                              "Somente o professor pode liberar.")

        if aluno["liberado"]:
            c.execute("UPDATE alunos SET liberado = 0 WHERE id = ?", (aluno_id,))

        c.execute("INSERT INTO saidas (aluno_id, saida) VALUES (?, ?)", (aluno_id, agora))
        return "saida", f"{aluno['nome']} saiu. Cronômetro de {fmt(LIMITE_SEGUNDOS)} iniciado."


# ---------- painel do professor ----------
def alunos_fora(agora=None):
    """Lista (nome, tempo_decorrido, atrasado) de quem está fora agora."""
    agora = agora or time.time()
    with conectar() as c:
        linhas = c.execute(
            """SELECT a.nome, s.saida FROM saidas s
               JOIN alunos a ON a.id = s.aluno_id
               WHERE s.retorno IS NULL ORDER BY s.saida"""
        ).fetchall()
    return [(l["nome"], agora - l["saida"], agora - l["saida"] > LIMITE_SEGUNDOS) for l in linhas]


def alunos_problema():
    with conectar() as c:
        return c.execute(
            "SELECT * FROM alunos WHERE estouros >= ? ORDER BY nome", (LIMITE_ESTOUROS,)
        ).fetchall()


def liberar_aluno(aluno_id):
    """Autoriza UMA saída do aluno, mesmo com 3 estouros. O contador não muda."""
    with conectar() as c:
        c.execute("UPDATE alunos SET liberado = 1 WHERE id = ?", (aluno_id,))


def zerar_contador(aluno_id):
    with conectar() as c:
        c.execute("UPDATE alunos SET estouros = 0, liberado = 0 WHERE id = ?", (aluno_id,))


def historico(aluno_id):
    with conectar() as c:
        return c.execute(
            "SELECT * FROM saidas WHERE aluno_id = ? ORDER BY saida DESC", (aluno_id,)
        ).fetchall()


# ---------- usadas pela interface web ----------
def estado_alunos():
    """Todos os alunos, com o instante da saída em aberto (None se estiver na sala)."""
    with conectar() as c:
        return c.execute(
            """SELECT a.id, a.nome, a.estouros, a.liberado, s.saida
               FROM alunos a
               LEFT JOIN saidas s ON s.aluno_id = a.id AND s.retorno IS NULL
               ORDER BY a.id"""
        ).fetchall()


def ultimo_instante():
    """Maior timestamp gravado no banco (0 se vazio)."""
    with conectar() as c:
        r = c.execute("SELECT MAX(saida) AS a, MAX(retorno) AS b FROM saidas").fetchone()
    return max(r["a"] or 0, r["b"] or 0)


def resetar_banco():
    with conectar() as c:
        c.execute("DELETE FROM saidas")
        c.execute("DELETE FROM alunos")