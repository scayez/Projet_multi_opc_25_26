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

        if multi_power_supply:
            multi_power_supply.powerDataUpdated.connect(self.run_simu)


        self.trajectoire = simulation(zmax=0.47287, phi=5000,champ_de_vue=0,ouverture=1)
        self.z = self.trajectoire.Init_Simu()



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

        (self.u,self.B) = self.trajectoire.simu(Icond1, Icond2, Iobj)

        # # Mise à jour des courbes
        self.curves[lens]['current'].setData(self.z, self.u)


    def update_plot(self, all_data):
        """Met à jour le graphique avec les nouvelles données"""
        current_time = time.time() - self.start_time
        
        # Liste des lentilles à afficher
        lenses_to_plot = {"Objective", "Condenser1", "Condenser2"}


        for lens, values in all_data.items():
            if lens not in lenses_to_plot:
                continue  # Ignore les autres lentilles

            try:
                i = float(values['current_out'].rstrip('A'))
            except ValueError:
                continue
                
            # Stockage des données
            self.data[lens]['time'].append(current_time)
            self.data[lens]['current'].append(i)
            
            # Limite à 500 points max
            if len(self.data[lens]['time']) > 500:
                for key in ['time', 'current']:
                    self.data[lens][key] = self.data[lens][key][-500:]
            
            # Crée les courbes si elles n'existent pas
            if lens not in self.curves:
                # Couleur basée sur l'index modulo le nombre de couleurs disponibles
                # color_idx = i % len(self.color_map)
                # base_color = self.color_map[color_idx]
                base_color = random.choice(self.color_map)
                
                # Tension = couleur pleine
                i_color = base_color

                
                self.curves[lens] = {
                    'current': self.plot_widget.plot(
                        pen=pg.mkPen(color=i_color, width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
                        name=f'{lens} - I'
                    )
                }
             
            # Lancement du calcul en arrière-plan
            #self.launch_calculation(lens, v, i, current_time)

            # # Mise à jour des courbes
            self.curves[lens]['current'].setData(self.data[lens]['time'], self.data[lens]['current'])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Création des widgets
    multi_power = MultiPowerSupplyWidget()
    simu = SimuWidget(multi_power_supply=multi_power)
    
    # Affichage
    multi_power.show()
    simu.show()
    
    sys.exit(app.exec())