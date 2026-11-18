import threading
import time


class Relogio:
    """Relógio da simulação: pode rodar mais rápido que o real (ex.: 10x)."""

    def __init__(self, inicio=None):
        self._lock = threading.Lock()
        self.vel = 1.0
        self._sim = inicio or time.time()
        self._real = time.time()

    def agora(self):
        with self._lock:
            return self._sim + (time.time() - self._real) * self.vel

    def definir_velocidade(self, v):
        with self._lock:
            atual = self._sim + (time.time() - self._real) * self.vel
            self._sim, self._real, self.vel = atual, time.time(), float(v)

    def avancar(self, segundos):
        with self._lock:
            self._sim += segundos

    def reiniciar(self):
        with self._lock:
            self._sim, self._real = time.time(), time.time()