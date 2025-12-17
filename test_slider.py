import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QButtonGroup
from PyQt6 import uic
from power_supply import PowerSupply
from PyQt6.QtCore import pyqtSignal, QObject

# Définir le chemin du fichier UI
dossier_courant = os.path.dirname(os.path.abspath(__file__))
qtCreatorFile = os.path.join(dossier_courant, "interface", "test_slider.ui")
# Vérifier que le fichier UI existe bien
if not os.path.exists(qtCreatorFile):
    raise FileNotFoundError(f"Fichier UI introuvable : {qtCreatorFile}")

class test_slider(QWidget):
    sliderValuesChanged = pyqtSignal(dict)  # Signal pour detecter les changements de valeur des sliders
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(qtCreatorFile, self)  # Charger l'UI
        # Initialiser les sliders
        self.init_sliders()

    def init_sliders(self):
        """
        Initialise et connecte les sliders pour le contrôle de tension et de courant.
        """

        # Définir les valeurs min/max des sliders en fonction des valeurs de l'alimentation
        self.slider.setMinimum(0)  
        self.slider.setMaximum(5)


        # Initialiser les sliders aux valeurs minimales (IMPORTANT !)
        self.slider.setValue(0)  

        self.slider.valueChanged.connect(self.slider_to_box)
        self.box.valueChanged.connect(self.box_to_slider)

    def slider_to_box(self, value):
        self.box.blockSignals(True)
        self.box.setValue(float(value))
        self.box.blockSignals(False)

    def box_to_slider(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(int(value))
        self.slider.blockSignals(False)

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = test_slider()
    window.show()
    sys.exit(app.exec())