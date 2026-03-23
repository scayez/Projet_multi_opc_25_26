import time

class PseudoAlim:
    def __init__(self, response_time: float = 0.2, Vmin=0, Vmax=5, Imin=0.0, Imax=1.0):
        self.response_time = response_time
        self.Vmin = Vmin
        self.Vmax = Vmax
        self.Imin = Imin
        self.Imax = Imax
        self.outputs_enabled = {}
        self.voltages = {}
        self.connected = False

    def open_connection(self):
        """Simule l'ouverture d'une connexion à l'alimentation."""
        time.sleep(self.response_time)
        self.connected = True
        print("[PseudoAlim] Connexion simulée ouverte.")
        return True  # Simule une réussite

    def enable_output(self, channel: int = 1):
        """Active la sortie pour un canal donné."""
        time.sleep(self.response_time)
        self.outputs_enabled[channel] = True
        print(f"[PseudoAlim] Sortie activée pour le canal {channel}.")

    def disable_output(self, channel: int = 1):
        """Désactive la sortie pour un canal donné."""
        time.sleep(self.response_time)
        self.outputs_enabled[channel] = False
        print(f"[PseudoAlim] Sortie désactivée pour le canal {channel}.")

    def set_voltage(self, voltage: float, channel: int = 1):
        """Simule la définition d’une tension sur un canal donné."""
        time.sleep(self.response_time)
        if not self.outputs_enabled.get(channel, False):
            print(f"[PseudoAlim] Avertissement : canal {channel} non activé !")
        if not self.Vmin <= voltage <= self.Vmax:
            raise ValueError(f"Tension {voltage} V hors limites [{self.Vmin}, {self.Vmax}]")
        self.voltages[channel] = voltage
        print(f"[PseudoAlim] Canal {channel} → Tension définie à {voltage:.3f} V")

    def get_voltage(self, channel: int = 1) -> float:
        """Retourne la tension appliquée sur le canal donné."""
        return self.voltages.get(channel, 0.0)

       