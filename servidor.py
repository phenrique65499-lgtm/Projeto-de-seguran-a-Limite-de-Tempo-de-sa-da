"""Inicia a interface web.

    python servidor.py              -> modo simulação (alunos de exemplo, relógio acelerável)
    python servidor.py --producao   -> usa o banco real (escola.db) e relógio em tempo real
"""
import argparse
import os
import threading
import webbrowser
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--producao", action="store_true", help="banco real e sem controles de simulação")
    p.add_argument("--porta", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 para acessar de outros aparelhos")
    p.add_argument("--sem-navegador", action="store_true", help="não abrir o navegador sozinho")
    a = p.parse_args()

    if not a.producao:
        os.environ["MODO_DEMO"] = "1"
        os.environ.setdefault("ESCOLA_DB", str(Path(__file__).parent / "escola_demo.db"))

    import uvicorn
    from api import achar_pagina, app  # importa só depois de definir as variáveis acima

    if achar_pagina() is None:
        print("ATENÇÃO: não encontrei static/index.html. A página não vai abrir até você criar a pasta "
              "'static' (ao lado do servidor.py) e colocar o index.html dentro dela.\n")

    url = f"http://127.0.0.1:{a.porta}"
    modo = "PRODUÇÃO" if a.producao else "SIMULAÇÃO"
    print(f"\nControle de saída da sala [{modo}] em {url}\n")
    if not a.sem_navegador:
        threading.Timer(1.2, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host=a.host, port=a.porta, log_level="info")


if __name__ == "__main__":
    main()