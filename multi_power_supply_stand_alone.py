import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6 import uic
from power_supply import PowerSupply
from power_supply_widget_stand_alone import PowerSupplyWidget
import json
from collections import defaultdict
from PyQt6.QtCore import pyqtSignal, QObject


# Chemin vers le fichier UI
dossier_courant = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(dossier_courant,"interface","multi_power_supply.ui")
if not os.path.exists(ui_file):
    raise FileNotFoundError(f"UI introuvable : {ui_file}")


class MultiPowerSupplyWidget(QWidget):
    powerDataUpdated = pyqtSignal(dict)  # Signal unique pour les U et I toutes les alimentations
    def __init__(self):
        super().__init__()
        uic.loadUi(ui_file, self)  # Charge les widgets promus automatiquement

        self.power_widgets = []  # pour garder la liste des PowerSupplyWidget
        self.lineEdit_password.textChanged.connect(self.check_password)
        self.checkBox_admin.stateChanged.connect(self.toggle_admin_mode)
        self.power_supply_params = self.load_power_supply_params()
        self.create_power_supplies(self.power_supply_params)

        self.lineEdit_password.setVisible(False)
        self.power_data = {}  # Dictionnaire pour stocker les dernières valeurs
        
    def create_power_supplies(self, params):
        """Crée dynamiquement les alimentations et configure les widgets."""
        # 1) Grouper par adresse
        groups = defaultdict(list)
        for p in params:
            addr = p["Adress"]
            groups[addr].append(p)

        # 2) Instancier chaque alimentation
        supplies = {}
        for addr, entries in groups.items():
            # bornes globales sur tous les canaux
            Vmin = min(e["Vmin"] for e in entries)
            Vmax = max(e["Vmax"] for e in entries)
            Imin = min(e["Imin"] for e in entries)
            Imax = max(e["Imax"] for e in entries)

            alim = PowerSupply(
                connection_mode="USB",
                address=addr,
                baud_rate=115200,
                Vmin=Vmin, Vmax=Vmax,
                Imin=Imin, Imax=Imax
            )
            if alim.open_connection() is None:
                raise RuntimeError(f"Connexion échouée pour l'alim {addr}")

            # on garde aussi un compteur de canal local à cette alim
            supplies[addr] = {"instance": alim, "next_channel": 1}

        # 3) Récupérer et trier les widgets promus
        widgets = self.findChildren(PowerSupplyWidget)
        widgets_sorted = sorted(
            widgets,
            key=lambda w: int(w.objectName().split('_')[-1])
        )

        # 4) Pour chaque entrée JSON, configurer le widget correspondant
        for idx, entry in enumerate(params):
            widget = widgets_sorted[idx]
            info = supplies[entry["Adress"]]
            ch = info["next_channel"]

            widget.setup(channel=ch, alim=info["instance"], lens=entry["Lens"])
            info["instance"].enable_output(channel=ch)
            info["next_channel"] += 1
            widget.setVisible(True)

            widget.set_voltage_slider_visible(False)
            self.power_widgets.append(widget)

        # 5) Masquer les widgets non utilisés
        for widget in widgets_sorted[len(params):]:
            widget.setVisible(False)

                # Après avoir créé les widgets, connecter leurs signaux
        for widget in self.power_widgets:
            widget.sliderValuesChanged.connect(self.handle_single_power_data)
        
    
    ##FAIRE LES CREATION D'ALIMS ICI AU LIEU DE L'INIT
    def load_power_supply_params(self, filename='power_supplies_params.json'):
        """Charge les paramètres depuis le fichier JSON"""
        print("Loading params")
        # Obtenir le chemin absolu du fichier JSON
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        print(f"Tentative de chargement depuis: {json_path}")
        
        with open(json_path, 'r') as f:
            params = json.load(f)
            return params

    def check_password(self, text):
        """Vérifie le mot de passe et active le bouton settings si correct"""
        # Mot de passe exemple - à remplacer par votre logique
        correct_password = "opc" 
        if text == correct_password:
            print('Ok pour rendre les Slider voltage visible')
            for widget in self.power_widgets:
                widget.set_voltage_slider_visible(True)

    def toggle_admin_mode(self, state):
        """Active/désactive le mode admin"""
        if state == Qt.CheckState.Checked.value:
            # Afficher le champ mot de passe
            self.lineEdit_password.setVisible(True)
            self.lineEdit_password.setFocus()
        else:
            self.lineEdit_password.setVisible(False)
            self.lineEdit_password.clear()
            # Masquer les sliders en quittant le mode admin

            for widget in self.power_widgets:
                widget.set_voltage_slider_visible(False)

    def collect_power_data(self):
        """Collecte les données de toutes les alimentations et émet un signal"""
        all_data = {}
        
        for widget in self.power_widgets:
            data = widget.update_settings()  # Cette méthode retourne maintenant les données
            if data:
                all_data[data['lens']] = data
        
        if all_data:
            self.powerDataUpdated.emit(all_data)

    def handle_single_power_data(self, data):
        """
        Stocke les données d'une alimentation et émet le signal global
        """
        # Mettre à jour les données pour cette lentille
        self.power_data[data['lens']] = data
        
        # Émettre le signal avec toutes les données actuelles
        self.powerDataUpdated.emit(self.power_data)


    def closeEvent(self, event):
        # Ici vous pouvez ajouter du code avant la fermeture
        print("La fenêtre est sur le point de se fermer")
        # self.alim_GPP2323.disable_output(channel=1)
        # self.alim_GPP2323.disable_output(channel=2)
        #self.alim_GPP1326.disable_output(channel=1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MultiPowerSupplyWidget()
    widget.show()
    sys.exit(app.exec())

