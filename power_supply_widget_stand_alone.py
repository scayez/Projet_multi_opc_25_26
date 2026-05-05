import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QButtonGroup
from PyQt6 import uic
from power_supply import PowerSupply
from PyQt6.QtCore import pyqtSignal, QObject

# Définir le chemin du fichier UI
dossier_courant = os.path.dirname(os.path.abspath(__file__))
qtCreatorFile = os.path.join(dossier_courant, "interface", "power_supply.ui")
# Vérifier que le fichier UI existe bien
if not os.path.exists(qtCreatorFile):
    raise FileNotFoundError(f"Fichier UI introuvable : {qtCreatorFile}")

class PowerSupplyWidget(QWidget):
    """Widget représentant l'interface de l'alimentation"""
    sliderValuesChanged = pyqtSignal(dict)  # Signal pour detecter les changements de valeur des sliders
    def __init__(self, parent=None, channel=1, alim=None, lens = 'Lentille1'):
        """
        Initialise le widget.
        
        :param parent: widget parent, None par défaut
        :param channel: numéro de canal de l'alimentation
        :param alim: instance de PowerSupply existante, ou None pour en créer une nouvelle
        :param lens: étiquette associée à l’alimentation (ex: Lentille1)
        """
        super().__init__(parent)
        uic.loadUi(qtCreatorFile, self)  # Charger l'UI
        self.channel = channel
        self.lens = lens
        if alim is None:
            # Mode stand-alone : création locale d’une alimentation PowerSupply
            self.alim =  PowerSupply(
                connection_mode="USB",
                address="ASRL4::INSTR",# Adresse série de l'appareil
                baud_rate=115200,
                Vmin=0, Vmax=100, #Les initialisations de tensions se font en mV
                Imin=0, Imax=100, # Les initialisations de courrant se font en mA
                channel=self.channel
                ) 
            # Ouverture de la connexion et affichage du nom du périphérique
            device_name = self.alim.open_connection()
            self.label_device.setText(str(device_name))
     

        else:
            # Mode intégré : alim passée par la MainWindow
            self.alim = alim
           
        # Initialiser les sliders
        self.init_sliders()
        #connecter l'alim et recupere son nom
        if self.alim.name:
            self.label_device.setText(str(self.alim.name))
            
        else:
            print("Attention : alim non connectée.")

        self.label_channel.setText(str(self.channel))
        self.label_lens.setText(str(self.lens))
   
    def setup(self, channel, alim, lens='lentille1'):
        """
        Configure le widget a posteriori (utile si instancié via promotion QtDesigner).
        
        :param channel: numéro de canal
        :param alim: instance de PowerSupply
        :param lens: étiquette associée
        """
        self.channel = channel
        self.alim = alim
        self.lens = lens
        # Mise à jour des labels
        if self.alim.name:
            self.label_device.setText(str(self.alim.name))
        else:
            self.label_device.setText("Appareil inconnu")

        self.label_channel.setText(str(self.channel))
        self.label_lens.setText(str(self.lens))

         # Maintenant que alim est bien défini avec ses bornes, on initialise les sliders
        self.init_sliders() #redéfini car appelé dans le fichier multi_power_supply_stand_alone si pas initialisé avant 
        # Affichage des bornes pour vérification (debug)
        print('-----------')
        print(self.alim.Vmin)
        print(self.alim.Vmax)
        print(self.alim.Imin)
        print(self.alim.Imax)
        print('-----------')
        

    def init_sliders(self):
        """
        Initialise et connecte les sliders pour le contrôle de tension et de courant.
        """

        # Définir les valeurs min/max des sliders en fonction des valeurs de l'alimentation
        self.Slider_voltage.setMinimum(int(self.alim.Vmin))  
        self.Slider_voltage.setMaximum(int(self.alim.Vmax))
        self.Slider_current.setMinimum(int(self.alim.Imin))
        self.Slider_current.setMaximum(int(self.alim.Imax))
        self.Voltage_incr.setMaximum(self.alim.Vmax/1000)
        self.Current_incr.setMaximum(self.alim.Imax/1000)
        self.Voltage_incr.setMinimum(self.alim.Vmin/1000)
        self.Current_incr.setMinimum(self.alim.Imin/1000)

        # Initialiser les sliders et box d'incrémentation aux valeurs minimales (IMPORTANT !)
        self.Slider_voltage.setValue(int(self.alim.Vmin))  # mV
        self.Slider_current.setValue(int(self.alim.Imin))  # mA
        self.Voltage_incr.setValue(self.alim.Vmin)  # mV
        self.Current_incr.setValue(self.alim.Imin)  # mA

        # Initialiser le step des sliders et box d'incrémentation
        self.Voltage_incr.setSingleStep((self.alim.Vmax - self.alim.Vmin) / (100*1000)) # step de 1% de la plage
        self.Current_incr.setSingleStep((self.alim.Imax - self.alim.Imin) / (100*1000))  # step de 1% de la plage


        # Initialiser les valeurs avec les minimums définis
        self.voltage_value = self.alim.Vmin / 1000 #Appel de la fonction dans le CB update_voltage
        self.current_value = self.alim.Imin / 1000
        # Afficher les valeurs initiales dans les labels en V et en A
        self.label_Vset.setText(f"Voltage : {self.alim.Vmin/1000:.2f}V")
        self.label_Iset.setText(f"Courant : {self.alim.Imin/1000:.3f}A")

        self.Slider_voltage.valueChanged.connect(self.update_voltage_from_slider)
        self.Slider_current.valueChanged.connect(self.update_current_from_slider)
        self.Slider_voltage.valueChanged.connect(self.on_slider_changed)
        self.Slider_current.valueChanged.connect(self.on_slider_changed)
        self.Voltage_incr.valueChanged.connect(self.update_voltage_from_box)
        self.Current_incr.valueChanged.connect(self.update_current_from_box)
        self.Voltage_incr.valueChanged.connect(self.on_slider_changed)
        self.Current_incr.valueChanged.connect(self.on_slider_changed)
        
    # --- Liaison sliders <-> spinbox ---
        self.Slider_voltage.valueChanged.connect(self.slider_to_box_voltage)
        self.Voltage_incr.valueChanged.connect(self.box_to_slider_voltage)
        self.Slider_current.valueChanged.connect(self.slider_to_box_current)
        self.Current_incr.valueChanged.connect(self.box_to_slider_current)

    def slider_to_box_voltage(self, value):
        # Slider (mV) -> Spinbox (V)
        self.Voltage_incr.blockSignals(True)
        self.Voltage_incr.setValue(value / 1000)
        self.Voltage_incr.blockSignals(False)

    def box_to_slider_voltage(self, value):
        # Spinbox (V) -> Slider (mV)
        self.Slider_voltage.blockSignals(True)
        self.Slider_voltage.setValue(int(value * 1000))
        self.Slider_voltage.blockSignals(False)

    def slider_to_box_current(self, value):
        # Slider (mA) -> Spinbox (A)
        self.Current_incr.blockSignals(True)
        self.Current_incr.setValue(value / 1000)
        self.Current_incr.blockSignals(False)

    def box_to_slider_current(self, value):
        # Spinbox (A) -> Slider (mA)
        self.Slider_current.blockSignals(True)
        self.Slider_current.setValue(int(value * 1000))
        self.Slider_current.blockSignals(False)

    def read_measurements(self): #PARTIE ROMAIN ET YANIS
        """Lit les valeurs mesurées (sans toucher aux consignes)."""
        settings = self.alim.get_settings(channel=self.channel)
        if not settings:
            return None

    # Mise à jour GUI locale
        self.label_Vmeas.setText(f'{settings["Voltage Out"]}')
        self.label_Imeas.setText(f'{settings["Current Out"]}')

        return {
            "lens": self.lens,
            "channel": self.channel,
            "voltage_set": settings["Voltage Set"],
            "current_set": settings["Current Set"],
            "voltage_out": settings["Voltage Out"],
            "current_out": settings["Current Out"]
        }


    def on_slider_changed(self):
        """Déclenché par n'importe quel slider"""
        self.update_settings()


    def update_voltage_from_slider(self, value):
        """
        Callback lorsque le slider de tension est modifié.
        Met à jour la tension de consigne (en V).
        """
        self.voltage_value = value/1000 
        self.update_settings()

    def update_current_from_slider(self, value):
        """
        Callback lorsque le slider de courant est modifié.
        Met à jour le courant de consigne (en A).
        """
        self.current_value = value/1000
        self.update_settings()

    def update_voltage_from_box(self, value):
        """Callback pour la box d'incrémentation de tension (en V)."""
        self.voltage_value = value
        self.update_settings()

    def update_current_from_box(self, value):
        """Callback pour la box d'incrémentation de courant (en A)."""
        self.current_value = value
        self.update_settings()
    
    def update_settings(self):
        """
        Met à jour les paramètres de l’alimentation et affiche les nouvelles valeurs.
        """
        updated_settings = self.alim.update_IV_set_point( #fonction qui demande à l'alim concernée de modifier la valeur des courants et tensions
        voltage_set_point = self.voltage_value,
        current_set_point = self.current_value,
        channel=self.channel 
        )
        

        if updated_settings:
            if updated_settings:
                # Émet les nouvelles valeurs
                self.sliderValuesChanged.emit({
                    'lens': self.lens,
                    'channel': self.channel,
                    'voltage_out': updated_settings["Voltage Out"],
                    'current_out': updated_settings["Current Out"]
                })


            # print("Réglages mis à jour :", updated_settings)
            self.label_Vmeas.setText(f'{updated_settings["Voltage Out"]}')
            self.label_Imeas.setText(f'{updated_settings["Current Out"]}')
            self.label_Vset.setText(f'{updated_settings["Voltage Set"]}V')
            self.label_Iset.setText(f'{updated_settings["Current Set"]}A')

       

    def set_voltage_slider_visible(self, visible: bool):
        """
        Affiche ou masque le slider de tension ainsi que les éléments associés.
        
        :param visible: booléen pour afficher (True) ou masquer (False)
        """
        self.Slider_voltage.setVisible(visible)
        self.Voltage_incr.setVisible(visible)
        self.label_Vset.setVisible(visible)
        self.label_Vmeas.setVisible(visible)
        self.label_voltage.setVisible(visible)
        self.line_voltage.setVisible(visible)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PowerSupplyWidget()
    window.show()
    sys.exit(app.exec())
