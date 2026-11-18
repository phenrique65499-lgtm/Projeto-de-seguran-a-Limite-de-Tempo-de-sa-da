"""Camada do sensor de digital.

Qualquer sensor só precisa ter um método ler_id() que devolve o ID do aluno
(ou None se a digital não for reconhecida).
"""


class SensorSimulado:
    """Para testar sem hardware: você digita o ID do aluno no terminal."""

    def ler_id(self):
        texto = input("Encoste o dedo (digite o ID do aluno): ").strip()
        return int(texto) if texto.isdigit() else None


class SensorAS608:
    """Esqueleto para sensores AS608/R307 (ex.: Raspberry Pi ou USB-serial).

    Requer: pip install adafruit-circuitpython-fingerprint pyserial
    Ajuste a porta serial (ex.: /dev/ttyUSB0 ou COM3) conforme seu hardware.
    """

    def __init__(self, porta="/dev/ttyUSB0", baud=57600):
        import serial
        import adafruit_fingerprint

        self._lib = adafruit_fingerprint
        self._finger = adafruit_fingerprint.Adafruit_Fingerprint(
            serial.Serial(porta, baudrate=baud, timeout=1)
        )

    def ler_id(self):
        print("Aguardando digital...")
        while self._finger.get_image() != self._lib.OK:
            pass
        if self._finger.image_2_tz(1) != self._lib.OK:
            return None
        if self._finger.finger_search() != self._lib.OK:
            return None
        return self._finger.finger_id  # ID gravado na memória do sensor