import pyvisa
import time

class PowerSupply:
    """
    Classe permettant de gérer une alimentation programmable via USB ou Ethernet
    en utilisant la bibliothèque PyVISA.

    Attributs principaux :
    - Modes de connexion : USB ou ETHERNET
    - Configuration de communication série
    - Limites de tension et courant (Vmin/Vmax, Imin/Imax)
    - Canal actif (par défaut : 1)
    """
    def __init__(self, 
                 connection_mode,      # "USB" ou "ETHERNET"
                 address,              # pour USB: port (ex: "ASRL3::INSTR"), pour Ethernet: adresse IP sous forme de "TCPIP0::192.168.1.10::INSTR"
                 baud_rate=115200, 
                 data_bits=8,
                 stop_bits=pyvisa.constants.StopBits.one,
                 parity=pyvisa.constants.Parity.none,
                 timeout=2000,
                 Vmin=0.0, Vmax=5000,
                 Imin=0.0, Imax=1000,
                 name=None,
                 channel =1): 

        """
        Initialise les paramètres de l'alimentation.

        :param connection_mode: Mode de connexion ("USB" ou "ETHERNET")
        :param address: Adresse du port ou IP de l'appareil
        :param baud_rate: Débit de communication
        :param data_bits: Nombre de bits de données
        :param stop_bits: Bits d'arrêt
        :param parity: Parité
        :param timeout: Délai d'attente en ms
        :param Vmin: Tension minimale autorisée (mV)
        :param Vmax: Tension maximale autorisée (mV)
        :param Imin: Courant minimal autorisé (mA)
        :param Imax: Courant maximal autorisé (mA)
        :param name: Nom de l'appareil (optionnel)
        :param channel: Canal actif par défaut
        """          
        self.connection_mode = connection_mode
        self.address = address
        self.baud_rate = baud_rate
        self.data_bits = data_bits
        self.stop_bits = stop_bits
        self.parity = parity
        self.timeout = timeout
        
        self.Vmin = Vmin
        self.Vmax = Vmax
        self.Imin = Imin
        self.Imax = Imax
        
        self.name = name
        
        self.rm = pyvisa.ResourceManager()
        self.instr = None  # instance de l'instrument

        self.channel = channel
        
    def open_connection(self):
        """
        Ouvre la connexion à l'alimentation via PyVISA.
        Initialise les paramètres de communication et bascule l'appareil en mode distant.
        Récupère l'identifiant de l'appareil si non fourni.
        :return: Nom de l'appareil connecté ou None en cas d'erreur
        """
        try:
            self.instr = self.rm.open_resource(self.address)
            self.instr.baud_rate = self.baud_rate
            self.instr.data_bits = self.data_bits
            self.instr.stop_bits = self.stop_bits
            self.instr.parity = self.parity
            self.instr.timeout = self.timeout
            
            # Mettre l'alim en mode Remote si nécessaire
            self.instr.write("SYSTem:REMote")
            # Récupérer l'ID si non fourni
            if self.name is None:
                self.name = self.instr.query("*IDN?").strip()
            print(f"Connecté à {self.name}")
        except Exception as e:
            print("Erreur de connexion :", e)
            self.name = None 

        return self.name

    def close_connection(self):
        """
        Ferme la connexion à l'instrument.
        """
        if self.instr:
            self.instr.close()
            self.instr = None

    def set_voltage(self, voltage, channel=None):
        """
        Définit la tension de sortie sur le canal spécifié.

        :param voltage: Tension souhaitée (en volts)
        :param channel: Canal à configurer (défaut : canal actif)
        """
        channel = channel if channel is not None else self.channel
        voltage_mV = voltage * 1000
        if voltage_mV < self.Vmin or voltage_mV > self.Vmax:
            print(f"Erreur: La tension doit être entre {self.Vmin/1000:.2f}V et {self.Vmax/1000:.2f}V.")
            return
        try:
            self.instr.write(f"VSET{channel}:{voltage:.3f}")
        except Exception as e:
            print("Erreur lors du réglage de la tension :", e)

    def set_current(self, current, channel=None):
        """
        Définit le courant limite sur le canal spécifié.

        :param current: Courant limite souhaité (en ampères)
        :param channel: Canal à configurer (défaut : canal actif)
        """
        channel = channel if channel is not None else self.channel
        current_mA = current * 1000
        if current_mA < self.Imin or current_mA > self.Imax:
            print(current_mA)
            print(f"Erreur: Le courant doit être entre {self.Imin/1000:.3f}A et {self.Imax/1000:.3f}A.")
            return
        try:
            self.instr.write(f"ISET{channel}:{current:.3f}")
        except Exception as e:
            print("Erreur lors du réglage du courant :", e)
      
    def enable_output(self, channel=None ):
        """
        Active la sortie du canal spécifié.

        :param channel: Numéro du canal ou "ALL" pour toutes les sorties
        """
        channel = channel if channel is not None else self.channel
        try:

            if channel == "ALL":
                self.instr.write("ALLOUTON")
                print(f":ALL OUTPut:STATe ON")
            else:

                self.instr.write(f":OUTPut{channel}:STATe ON")
                print(f":OUTPut{channel}:STATe ON")
            time.sleep(0.1)
        except Exception as e:
            print("Erreur lors de l'activation de la sortie :", e)
    
    def disable_output(self, channel=None):
        """
        Désactive la sortie du canal spécifié.

        :param channel: Canal à désactiver (défaut : canal actif)
        """
        try:
          
            self.instr.write(f":OUTPut{channel}:STATe OFF")
            time.sleep(0.1)
        except Exception as e:
            print("Erreur lors de la désactivation de la sortie :", e)
    
    def get_settings(self, channel=None):
        """
        Récupère les réglages actuels et les valeurs mesurées de tension et de courant.

        :param channel: Canal à interroger (défaut : canal actif)
        :return: Dictionnaire avec les valeurs configurées et mesurées, ou None si erreur
        """
        channel = channel if channel is not None else self.channel
        try:
            voltage_set = self.instr.query(f"VSET{channel}?").strip()
            current_set = self.instr.query(f"ISET{channel}?").strip()
            voltage_out = self.instr.query(f"VOUT{channel}?").strip()  
            current_out = self.instr.query(f"IOUT{channel}?").strip()  
            return {
                "Voltage Set": voltage_set,
                "Current Set": current_set,
                "Voltage Out": voltage_out,
                "Current Out": current_out,
                "Name": self.name
            }
        except Exception as e:
            print("Erreur lors de la récupération des réglages :", e)
            return None

    def update_IV_set_point(self, voltage_set_point, current_set_point, channel=None):
        """
        Met à jour à la fois la tension et le courant limite du canal spécifié.

        :param voltage_set_point: Tension (V)
        :param current_set_point: Courant (A)
        :param channel: Canal à mettre à jour
        :return: Dictionnaire des nouveaux réglages
        """
        ch = channel if channel is not None else self.channel
        self.set_voltage(voltage_set_point, ch)
        self.set_current(current_set_point, ch)
        return self.get_settings(ch)
    
    # D'autres méthodes utiles pourraient être ajoutées, par exemple :
    def query_mode(self):
        """
        Interroge le mode de fonctionnement actuel de l'alimentation.

        :return: "CV" (tension constante), "CC" (courant constant), ou None si erreur
        """
        try:
            mode = self.instr.query("MODE?").strip()
            return mode
        except Exception as e:
            print("Erreur lors de la requête du mode :", e)
            return None

    def disable_protections(self):
        """
        Méthode pour désactiver les protections OVP et OCP si nécessaire.
        """
        try:
            self.instr.write("OVP OFF")
            self.instr.write("OCP OFF")
        except Exception as e:
            print("Erreur lors de la désactivation des protections :", e)
            
