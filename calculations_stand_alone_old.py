

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                            QPushButton, QWidget, QApplication, QMessageBox)
import os
from PyQt6 import uic
import sys
from power_supply_widget_stand_alone import PowerSupplyWidget
from multi_power_supply_stand_alone import MultiPowerSupplyWidget

# Chargement du fichier .ui contenant l'interface graphique
dossier_courant = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(dossier_courant,"interface","calculations.ui")
if not os.path.exists(ui_file):
    raise FileNotFoundError(f"UI introuvable : {ui_file}")

class CalculationsWidget(QWidget):
    """
    Widget PyQt permettant de configurer et gérer une liste d'alimentations.
    Permet d’ajouter, visualiser, supprimer et sauvegarder des alimentations via une interface graphique.
    """
    def __init__(self,  parent=None):
        """
        Initialise l'interface utilisateur, connecte les boutons à leurs actions
        et initialise la liste d'alimentations.
        """
        super().__init__(parent)
        uic.loadUi(ui_file, self)
        # Connecter le signal pour recuperer les valeurs de U et I des alims

 
   

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = CalculationsWidget()
    widget.show()
    sys.exit(app.exec())
