import time
import random
import nidaqmx
import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration, Edge
from nidaqmx.stream_writers import AnalogMultiChannelWriter

class NiDetectorAcquisition:

    def __init__(self, channel_read: str, min_voltage: float = 0.0, max_voltage: float = 10.0):
        """
        Initialise l'acquisition analogique avec nidaqmx.

        Args:
            channel_read (str): Nom du canal analogique, ex: "Dev1/ai0"
            min_voltage (float): Tension minimale attendue.
            max_voltage (float): Tension maximale attendue.
            response_time (float): Délai artificiel pour simuler le temps de réponse.
        """
        self.channel_read = channel_read
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage
        #self.response_time = response_time
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(
            channel_read,
            min_val=min_voltage,
            max_val=max_voltage,
            #terminal_config=TerminalConfiguration.DIFF
            terminal_config=TerminalConfiguration.RSE
        )

    def read_gray_level(self) -> int:
        """
        Lit une tension entre 0 et 10 V et la convertit en niveau de gris [0–255].

        Returns:
            int: Niveau de gris simulé.
        """
       
        #time.sleep(self.response_time)
        voltage = self.task.read()
        voltage_clamped = max(self.min_voltage, min(self.max_voltage, voltage))  # clamp entre 0 et 10 V
        gray_level = int(255 * (voltage_clamped - self.min_voltage) / (self.max_voltage - self.min_voltage))
        print(voltage)

        return gray_level


    def close(self):
        """Ferme proprement la tâche NI."""
        self.task.close()


