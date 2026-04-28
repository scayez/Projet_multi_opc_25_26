from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6 import uic
import pyqtgraph as pg
from collections import defaultdict
import time
import sys
import os
import random
from multi_power_supply_stand_alone import MultiPowerSupplyWidget
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from main import simulation

# Chargement du fichier .ui contenant l'interface graphique
dossier_courant = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(dossier_courant,"interface","calculations.ui") # change this path if your .ui file is located elsewhere
if not os.path.exists(ui_file):
    raise FileNotFoundError(f"UI introuvable : {ui_file}")

class SimuWidget(QWidget):
    def __init__(self, multi_power_supply=None, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_file, self)
        
        # Initialisation
        # Configuration minimale du graphique
        self.plot_widget.clear()

        # Rotation du graphique pour avoir un affichage de haut en bas
        self.plot_widget.getViewBox().setAspectLocked(False)
        self.plot_widget.getViewBox().setRotation(90)

        self.plot_widget.setLabel('left', 'Hauteur du rayon')
        self.plot_widget.setLabel('bottom', 'z (m)')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)

        self.color_map = [
            (255, 0, 0),    # Rouge
            (0, 0, 255),    # Bleu
            (0, 128, 0),    # Vert
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 128, 0),  # Orange
            (128, 0, 255),  # Violet
            (0, 255, 0)     # Vert vif
        ]

        self.curves = {}

        # Configuration des minimums et maximums
        self.box_beam_energy.setMaximum(25000)
        self.box_field.setMaximum(1)
        self.box_aperture.setMaximum(1)
        self.box_beam_energy.setMinimum(0)
        self.box_field.setMinimum(0)
        self.box_aperture.setMinimum(0)
        self.box_screen_position.setMinimum(0)

        # Valeurs par défaut
        self.box_screen_position.setValue(0.47287)
        self.box_beam_energy.setValue(5000)
        self.box_field.setValue(0)
        self.box_aperture.setValue(1)

        zmax = self.box_screen_position.value()
        phi = self.box_beam_energy.value()
        champ_de_vue = self.box_field.value()
        ouverture = self.box_aperture.value()

        self.box_screen_position.valueChanged.connect(self.update_simulation_params)
        self.box_beam_energy.valueChanged.connect(self.update_simulation_params)
        self.box_field.valueChanged.connect(self.update_simulation_params)
        self.box_aperture.valueChanged.connect(self.update_simulation_params)

        self.trajectoire = simulation(zmax, phi,champ_de_vue,ouverture)
        self.z = self.trajectoire.Init_Simu()

        self.all_data = {}  # Pour stocker les dernières données reçues

        if multi_power_supply:
            multi_power_supply.powerDataUpdated.connect(self._update_all_data)

        # Thread de simulation
        self.simu_thread = SimuThread(self._get_all_data)
        self.simu_thread.dataReady.connect(self.run_simu)
        self.simu_thread.start()


    # Mise à jour des paramètres de la simulation lorsque les valeurs changent
    def update_simulation_params(self):
        zmax = self.box_screen_position.value()
        phi = self.box_beam_energy.value()
        champ_de_vue = self.box_field.value()
        ouverture = self.box_aperture.value()

        self.trajectoire = simulation(zmax, phi, champ_de_vue, ouverture)
        self.z = self.trajectoire.Init_Simu()

    # Méthodes pour le thread de simulation
    def _update_all_data(self, all_data):
        self.all_data = all_data

    # Méthode pour que le thread puisse accéder aux données les plus récentes
    def _get_all_data(self):
        return self.all_data

       
    def closeEvent(self, event):
        self.simu_thread.stop()
        event.accept()

    # Méthode pour exécuter la simulation et mettre à jour le graphique
    def run_simu(self, all_data):

                # Liste des lentilles à afficher
        lenses_to_plot = {"Objective", "Condenser1", "Condenser2"}

        Iobj = None
        Icond1 = None
        Icond2 = None

        for lens, values in all_data.items():
            if lens not in lenses_to_plot:
                continue  # Ignore les autres lentilles

            try:
                i = float(values['current_out'].rstrip('A'))
            except ValueError:
                continue

            if lens == "Objective":
                Iobj = i
            elif lens == "Condenser1":
                Icond1 = i
            elif lens == "Condenser2":
                Icond2 = i

        self.label_Icond1.setValue(Icond1)
        self.label_Icond2.setValue(Icond2)
        self.label_Iobj.setValue(Iobj)

        (self.u,self.B) = self.trajectoire.simu(Icond1, Icond2, Iobj)

        #Création de la courbe de simulation si elle n'existe pas encore
        if "simu" not in self.curves:
            self.curves["simu"] = {
                'current': self.plot_widget.plot(
                    pen=pg.mkPen(color=(255, 0, 0), width=2),  # couleur et style à adapter
                    name='Simulation'
                )
            }
        
        # Mise à jour des courbes
        self.curves["simu"]['current'].setData(self.z, self.u)

class SimuThread(QThread):
    dataReady = pyqtSignal(dict)  # Signal pour transmettre les résultats

    def __init__(self, get_data_func, interval=0.2, parent=None): #Pour changer la fréquence de mise à jour, ajustez l'intervalle (en secondes)
        super().__init__(parent)
        self.get_data_func = get_data_func  # Fonction pour obtenir les données à simuler
        self.interval = interval
        self._run_flag = True

    def run(self):
        while self._run_flag:
            all_data = self.get_data_func()
            if all_data:
                self.dataReady.emit(all_data)
            time.sleep(self.interval)

    def stop(self):
        self._run_flag = False
        self.wait()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Création des widgets
    multi_power = MultiPowerSupplyWidget()
    simu = SimuWidget(multi_power_supply=multi_power)
    
    # Affichage
    multi_power.show()
    simu.show()
    
    sys.exit(app.exec())