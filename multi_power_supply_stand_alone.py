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
from PyQt6.QtCore import QTimer




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

        self.scan_running = False  # Flag pour indiquer si un scan est en cours

        self.lineEdit_password.setVisible(False)
        self.power_data = {}  # Dictionnaire pour stocker les dernières valeurs

        #PARTIE ROMAIN ET YANIS
        """Utilisation d'un timer pour récupérer les valeurs toutes les 500ms et non plus seulement lorsqu'on bouge les sliders"""
        self.timer = QTimer() 
        self.timer.timeout.connect(self.collect_power_data)
        self.timer.start(500)  # toutes les 500 ms

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

            # Initialiser la tension à Vdef si elle est définie, sinon à Vmin
            Vdef = entry.get("Vdef", info["instance"].Vmin)
            Idef = entry.get("Idef", info["instance"].Imin)  # Optionnel, si tu veux aussi le courant
            try:
                widget.alim.update_IV_set_point(voltage_set_point=Vdef/1000, current_set_point=Idef/1000 if Idef else widget.alim.Imin/1000, channel=ch)
                widget.Slider_voltage.setValue(int(Vdef))
                widget.Voltage_incr.setValue(Vdef/1000)
            except Exception as e:
                print(f"Erreur lors de l'init de la tension par défaut pour {entry['Lens']} : {e}")

            # widget.set_voltage_slider_visible(False)
            widget.set_voltage_slider_visible(False)
            self.power_widgets.append(widget)

        # 5) Masquer les widgets non utilisés
        for widget in widgets_sorted[len(params):]:
            widget.setVisible(False)
        
                # Après avoir créé les widgets, connecter leurs signaux
        for widget in self.power_widgets:
            widget.sliderValuesChanged.connect(self.handle_single_power_data)
        
    
    ##FAIRE LES CREATIONS D'ALIMS ICI AU LIEU DE L'INIT
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

    
    def collect_power_data(self): #PARTIE ROMAIN ET YANIS
        """Récupère les vraies mesures de chaque widget."""
        all_data = {}

        for widget in self.power_widgets:
            data = widget.read_measurements()
            if data:
                all_data[data["lens"]] = data

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

            # Mettre toutes les alimentations à 0V et 0A
        if not getattr(self, "scan_running", False):
            # Désactiver les voies seulement si pas de scan en cours, sinon laisser les réglages pour le prochain scan
            for widget in self.power_widgets:
                try:
                    widget.alim.update_IV_set_point(
                        voltage_set_point=0,
                        current_set_point=0,
                        channel=widget.channel
                    )
                    widget.Slider_voltage.setValue(0)
                    widget.Voltage_incr.setValue(0)
                    widget.Slider_current.setValue(0)
                    widget.Current_incr.setValue(0)
                    # Désactiver la sortie de la voie
                    widget.alim.disable_output(channel=widget.channel)
                except Exception as e:
                    print(f"Erreur lors de la mise à 0/désactivation de l'alim {getattr(widget, 'lens', '?')}: {e}")
        else:
            print("Scan en cours : les voies restent actives.")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MultiPowerSupplyWidget()
    widget.show()
    sys.exit(app.exec())

