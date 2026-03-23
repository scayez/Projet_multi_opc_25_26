from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                            QPushButton, QWidget, QApplication, QMessageBox)
import os
from PyQt6 import uic
import sys
import json

# Chargement du fichier .ui contenant l'interface graphique
dossier_courant = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(dossier_courant,"interface","settings.ui")
if not os.path.exists(ui_file):
    raise FileNotFoundError(f"UI introuvable : {ui_file}")

class SettingsWidget(QWidget):
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
        self.pushButton_add_power_supply.clicked.connect(self.add_power_supply)
        self.pushButton_Finish.clicked.connect(self.finish)
        self.pushButton_preview.clicked.connect(self.preview_power_supplies)
        self.pushButton_delete.clicked.connect(self.delete_power_supply)

        self.power_supplies = []  # Liste pour stocker toutes les alimentations

    def add_power_supply(self):
        """
        Ajoute une alimentation à la liste après avoir vérifié l'absence de doublons
        sur l'identifiant (ID) et la lentille (Lens). Enregistre ensuite les données dans un fichier JSON.
        """
        current_id = self.comboBox_Id.currentText()
        current_lens = self.comboBox_lens.currentText()

        # Vérification des doublons
        if any(p['Id'] == current_id for p in self.power_supplies):
            QMessageBox.warning(self, "Erreur", f"L'ID '{current_id}' est déjà utilisé.")
            return
        if any(p['Lens'] == current_lens for p in self.power_supplies):
            QMessageBox.warning(self, "Erreur", f"La lentille '{current_lens}' est déjà utilisée.")
            return

        # Lecture des valeurs
        Vmin = self.doubleSpinBox_Vmin.value() * 1000
        Vmax = self.doubleSpinBox_Vmax.value() * 1000
        Imin = self.doubleSpinBox_Imin.value() * 1000
        Imax = self.doubleSpinBox_Imax.value() * 1000

        # Vérification des bornes
        if Vmin > Vmax:
            QMessageBox.warning(self, "Erreur", "Vmin ne peut pas être supérieur à Vmax.")
            return
        if Imin > Imax:
            QMessageBox.warning(self, "Erreur", "Imin ne peut pas être supérieur à Imax.")
            return

        # Création du dictionnaire contenant les paramètres de l'alimentation
        new_power_supply = {
            'Lens': current_lens,
            'Id': current_id,
            'Adress': self.get_address_from_id(current_id),
            'Channel': self.get_channel_from_id(current_id),
            'Vmin': Vmin,
            'Vmax': Vmax,
            'Imin': Imin,
            'Imax': Imax,
            }

        self.power_supplies.append(new_power_supply)
        self.save_to_json()
        print(f"Alimentation ajoutée : {new_power_supply}")

    def save_to_json(self, filename='power_supplies_params.json'):
        """
        Sauvegarde la liste des alimentations dans un fichier JSON.
        :param filename: Nom du fichier dans lequel les données seront enregistrées.
        """
        with open(filename, 'w') as f:
            json.dump(self.power_supplies, f, indent=4)

    def get_address_from_id(self, power_supply_id):
        """
        Retourne l'adresse VISA correspondant à l'identifiant de l'alimentation.
        :param power_supply_id: Identifiant de l'alimentation.
        :return: Adresse VISA (chaîne de caractères).
        """
        if "GPP-2323 #1" in power_supply_id:
            return "ASRL5::INSTR"
        elif "GPP-2323 #2" in power_supply_id:
            return "ASRL4::INSTR"
        elif power_supply_id == "GPP-1326":
            return "ASRL6::INSTR"
        else:
            return "UNKNOWN_ADDRESS"

    def get_channel_from_id(self, power_supply_id):
        """
        Détermine le numéro de canal à partir de l'identifiant de l'alimentation.
        :param power_supply_id: Identifiant de l'alimentation.
        :return: Numéro du canal (int) ou None si inconnu.
        """
        if "Channel1" in power_supply_id:
            return 1
        elif "Channel2" in power_supply_id:
            return 2
        else:
            return None


    def preview_power_supplies(self):
        """
        Affiche dans une boîte de dialogue les alimentations sauvegardées
        dans le fichier JSON, sous forme lisible.
        """
        filename = 'power_supplies_params.json'
        
        if not os.path.exists(filename):
            QMessageBox.information(self, "Preview", "No Power Supply Saved.")
            return
        try:
            with open(filename, 'r') as f:
                data = json.load(f)     
            if not data:
                QMessageBox.information(self, "Preview", "Power supply list is empty.")
                return

            # Construction du message à afficher
            message = ""
            for i, alim in enumerate(data, start=1):
                message += (
                    f"[{i}] Lens: {alim['Lens']}, ID: {alim['Id']}, "
                    f"Adresse: {alim['Adress']}, Channel: {alim['Channel']}\n"
                    f"Vmin: {alim['Vmin']} mV, Vmax: {alim['Vmax']} mV\n"
                    f"Imin: {alim['Imin']} mA, Imax: {alim['Imax']} mA\n\n"
                )

            QMessageBox.information(self, "Power Supply Saved", message)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible to read JSON file:\n{str(e)}")

    def delete_power_supply(self):
        """
        Supprime une alimentation sélectionnée dans une boîte de dialogue déroulante
        depuis le fichier JSON des paramètres sauvegardés.
        """
        filename = 'power_supplies_params.json'

        if not os.path.exists(filename):
            QMessageBox.information(self,  "Delete", "No saved power supplies found.")
            return

        with open(filename, 'r') as f:
            data = json.load(f)

        if not data:
            QMessageBox.information(self,  "Delete", "The power supply list is empty.")
            return

        # Création d'une petite fenêtre de sélection
        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Power Supply")
        layout = QVBoxLayout()

        label = QLabel("Select a power supply to delete:")
        layout.addWidget(label)

        combo = QComboBox()
        items = [f"{p['Lens']} ({p['Id']})" for p in data]
        combo.addItems(items)
        layout.addWidget(combo)

        btn_delete = QPushButton("Delete")
        layout.addWidget(btn_delete)

        def on_delete():
            index = combo.currentIndex()
            if index >= 0:
                del data[index]
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)
                QMessageBox.information(self, "Delete", "Power supply delete.")
                dialog.accept()
            else:
                QMessageBox.warning(self, "Error", "No power supply selected.")

        btn_delete.clicked.connect(on_delete)
        dialog.setLayout(layout)
        dialog.exec()

    def finish(self):
        """
        Ferme le widget après avoir vérifié qu'au moins une alimentation a été ajoutée.
        """
      
        if len(self.power_supplies) == 0:
            QMessageBox.warning(self, "Attention", "No power supply selected")
            return
        self.close()
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = SettingsWidget()
    widget.show()
    sys.exit(app.exec())


       