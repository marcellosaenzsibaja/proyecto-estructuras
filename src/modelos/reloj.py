from src.estructuras_datos.agenda import Agenda, Evento

class MotorReloj:

    def __init__(self):
        self.agenda = Agenda()
        self.tiempo_virtual = 0
        self.contador_secuencia = 0

    def esta_vacio(self) -> bool:
        return self.agenda.esta_vacio()

    def _siguiente_secuencia(self) -> int:
        self.contador_secuencia += 1
        return self.contador_secuencia

    def programar_evento(self, intervalo: int, tipo: str, carga=None) -> Evento:
        evento = Evento(self.tiempo_virtual + intervalo, self._siguiente_secuencia(), tipo, carga)
        self.agenda.insertar(evento)
        return evento

    def cancelar_evento(self, evento: Evento) -> bool:
        return self.agenda.cancelar(evento)

    def reprogramar_evento(self, evento: Evento, nuevo_tiempo: int):
        self.agenda.reprogramar(evento, nuevo_tiempo, self._siguiente_secuencia())

    def siguiente_evento(self):
        if self.agenda.esta_vacio():
            return None
        evento = self.agenda.extraer_minimo()
        self.tiempo_virtual = evento.tiempo
        return evento
