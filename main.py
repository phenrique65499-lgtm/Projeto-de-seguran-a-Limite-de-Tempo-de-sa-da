import os
from getpass import getpass

import banco
import regras
from sensor import SensorSimulado

PIN_PROFESSOR = os.environ.get("PIN_PROFESSOR", "1234")


def criar_sensor():
    if os.environ.get("SENSOR") == "real":
        from sensor import SensorAS608
        return SensorAS608(os.environ.get("PORTA_SENSOR", "/dev/ttyUSB0"))
    return SensorSimulado()


# ---------------- porta (sensor) ----------------
def modo_porta(sensor):
    print("\n[MODO PORTA] Ctrl+C para voltar ao menu.\n")
    try:
        while True:
            aluno_id = sensor.ler_id()
            if aluno_id is None:
                print("Digital não reconhecida.\n")
                continue
            _, msg = regras.passar_digital(aluno_id)
            print(msg + "\n")
    except KeyboardInterrupt:
        print()


# ---------------- professor ----------------
def painel_professor():
    if getpass("PIN do professor: ") != PIN_PROFESSOR:
        print("PIN incorreto.")
        return

    while True:
        print("\n=== PAINEL DO PROFESSOR ===")
        print("1) Quem está fora agora")
        print("2) Alunos problema")
        print("3) Liberar aluno problema (autoriza 1 saída)")
        print("4) Zerar contador de um aluno")
        print("5) Histórico de um aluno")
        print("0) Voltar")
        op = input("> ").strip()

        if op == "1":
            fora = regras.alunos_fora()
            if not fora:
                print("Ninguém fora da sala.")
            for nome, tempo, atrasado in fora:
                aviso = "  <-- PASSOU DE 3 MIN" if atrasado else ""
                print(f"- {nome}: {regras.fmt(tempo)}{aviso}")

        elif op == "2":
            lista = regras.alunos_problema()
            if not lista:
                print("Nenhum aluno problema.")
            for a in lista:
                status = "liberado p/ 1 saída" if a["liberado"] else "bloqueado"
                print(f"- [{a['id']}] {a['nome']} | estouros: {a['estouros']} | {status}")

        elif op == "3":
            aluno_id = input("ID do aluno: ").strip()
            if aluno_id.isdigit():
                regras.liberar_aluno(int(aluno_id))
                print("Aluno liberado para uma saída.")

        elif op == "4":
            aluno_id = input("ID do aluno: ").strip()
            if aluno_id.isdigit():
                regras.zerar_contador(int(aluno_id))
                print("Contador zerado.")

        elif op == "5":
            aluno_id = input("ID do aluno: ").strip()
            if aluno_id.isdigit():
                import time
                for s in regras.historico(int(aluno_id)):
                    saida = time.strftime("%d/%m %H:%M:%S", time.localtime(s["saida"]))
                    if s["retorno"] is None:
                        print(f"- {saida} | ainda fora")
                    else:
                        dur = regras.fmt(s["retorno"] - s["saida"])
                        print(f"- {saida} | {dur}{' (ESTOUROU)' if s['estourou'] else ''}")

        elif op == "0":
            return


# ---------------- cadastro ----------------
def cadastrar():
    aluno_id = input("ID do aluno (o mesmo gravado no sensor): ").strip()
    nome = input("Nome: ").strip()
    if aluno_id.isdigit() and nome:
        try:
            regras.cadastrar_aluno(int(aluno_id), nome)
            print("Aluno cadastrado.")
        except Exception:
            print("Já existe um aluno com esse ID.")
    else:
        print("Dados inválidos.")


def main():
    banco.iniciar()
    sensor = criar_sensor()
    while True:
        print("\n=== CONTROLE DE SAÍDA DA SALA ===")
        print("1) Modo porta (sensor de digital)")
        print("2) Painel do professor")
        print("3) Cadastrar aluno")
        print("0) Sair")
        op = input("> ").strip()
        if op == "1":
            modo_porta(sensor)
        elif op == "2":
            painel_professor()
        elif op == "3":
            cadastrar()
        elif op == "0":
            break


if __name__ == "__main__":
    main()