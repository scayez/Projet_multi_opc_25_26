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

# Chargement du fichier .ui contenant l'interface graphique
dossier_courant = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(dossier_courant,"interface","calculations.ui")
if not os.path.exists(ui_file):
    raise FileNotFoundError(f"UI introuvable : {ui_file}")

class CalculationsWidget(QWidget):
    def __init__(self, multi_power_supply=None, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_file, self)
        
        # Initialisation
        self.data = defaultdict(lambda: {'time': [], 'voltage': [], 'current': []})
        self.start_time = time.time()
        
        # Configuration minimale du graphique
        self.plot_widget.clear()
        self.plot_widget.setLabel('left', 'Tension (V)')
        self.plot_widget.setLabel('bottom', 'Temps (s)')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)

         # Colormap prédéfinie (teintes régulièrement espacées)
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
        
        # Dictionnaire pour stocker les courbes
        self.curves = {}  # Format: {lens: {'voltage': curve, 'current': curve}}
        
        # Connexion au signal
        if multi_power_supply:
            multi_power_supply.powerDataUpdated.connect(self.update_plot)

        # # Ajouter pour les résultats de calcul
        # self.calculation_results = defaultdict(lambda: {'time': [], 'value': []})
        # self.calculation_workers = {}  # Pour garder une référence aux workers
        # self.calculation_curves = {}   # Courbes des résultats

    def update_plot(self, all_data):
        """Met à jour le graphique avec les nouvelles données"""
        current_time = time.time() - self.start_time
        
        for lens, values in all_data.items():
            # Conversion des valeurs
            try:
                v = float(values['voltage'].rstrip('V'))
                i = float(values['current'].rstrip('A'))
            except ValueError:
                continue
                
            # Stockage des données
            self.data[lens]['time'].append(current_time)
            self.data[lens]['voltage'].append(v)
            self.data[lens]['current'].append(i)
            
            # Limite à 500 points max
            if len(self.data[lens]['time']) > 500:
                for key in ['time', 'voltage', 'current']:
                    self.data[lens][key] = self.data[lens][key][-500:]
            
            # Crée les courbes si elles n'existent pas
            if lens not in self.curves:
                # Couleur basée sur l'index modulo le nombre de couleurs disponibles
                # color_idx = i % len(self.color_map)
                # base_color = self.color_map[color_idx]
                base_color = random.choice(self.color_map)
                
                # Tension = couleur pleine
                v_color = base_color
                # Courant = version plus claire
                i_color = tuple(min(c + 50, 255) for c in base_color)
                
                self.curves[lens] = {
                    'voltage': self.plot_widget.plot(
                        pen=pg.mkPen(color=v_color, width=2),
                        name=f'{lens} - V'
                    ),
                    'current': self.plot_widget.plot(
                        pen=pg.mkPen(color=i_color, width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
                        name=f'{lens} - I'
                    )
                }
             
            # Lancement du calcul en arrière-plan
            #self.launch_calculation(lens, v, i, current_time)

            # # Mise à jour des courbes
            self.curves[lens]['voltage'].setData(self.data[lens]['time'], self.data[lens]['voltage'])
            self.curves[lens]['current'].setData(self.data[lens]['time'], self.data[lens]['current'])
            # Mise à jour de toutes les courbes
            #self.update_all_curves()


#     def launch_calculation(self, lens, voltage, current, timestamp):
#         """Démarre un nouveau calcul dans un thread séparé"""
#         # Arrête le calcul précédent si existant
#         if lens in self.calculation_workers:
#             self.calculation_workers[lens].quit()
#             self.calculation_workers[lens].wait()
        
#         # Crée et démarre un nouveau worker
#         worker = CalculationWorker(lens, voltage, current)
#         worker.result_ready.connect(self.handle_calculation_result)
#         self.calculation_workers[lens] = worker
#         worker.start()

#     @pyqtSlot(str, float)
#     def handle_calculation_result(self, lens, result):
#         """Reçoit les résultats des calculs et met à jour les données"""
#         current_time = time.time() - self.start_time
        
#         # Stockage du résultat
#         self.calculation_results[lens]['time'].append(current_time)
#         self.calculation_results[lens]['value'].append(result)
        
#         # Limite l'historique
#         if len(self.calculation_results[lens]['time']) > 500:
#             for key in ['time', 'value']:
#                 self.calculation_results[lens][key] = self.calculation_results[lens][key][-500:]
        
#         # Mise à jour de la courbe
#         self.update_calculation_curve(lens)

#     def update_calculation_curve(self, lens):
#         """Crée ou met à jour la courbe de résultats"""
#         if lens not in self.calculation_curves:
#             # Crée une nouvelle courbe (style différent)
#             self.calculation_curves[lens] = self.plot_widget.plot(
#                 pen=pg.mkPen(color=(0, 0, 0), width=2, style=pg.QtCore.Qt.PenStyle.DotLine),
#                 name=f'{lens} - Résultat'
#             )
        
#         # Met à jour les données
#         self.calculation_curves[lens].setData(
#             self.calculation_results[lens]['time'],
#             self.calculation_results[lens]['value']
#         )

#     def update_all_curves(self):
#         """Met à jour toutes les courbes"""
#         for lens in self.curves:
#             self.curves[lens]['voltage'].setData(self.data[lens]['time'], self.data[lens]['voltage'])
#             self.curves[lens]['current'].setData(self.data[lens]['time'], self.data[lens]['current'])
        
#         for lens in self.calculation_curves:
#             self.update_calculation_curve(lens)



# class CalculationWorker(QThread):
#     result_ready = pyqtSignal(str, float)  # lens, result
    
#     def __init__(self, lens, voltage, current):
#         super().__init__()
#         self.lens = lens
#         self.voltage = voltage
#         self.current = current
    
#     def run(self):
#         """Simule un calcul long et retourne un résultat"""
#         # Simulation d'un calcul lourd (3-5 secondes)
#         processing_time = 3 + 2 * random.random()
#         time.sleep(processing_time)
        
#         # Exemple de calcul (à remplacer par votre vrai calcul)
#         result = self.voltage * self.current * random.uniform(0.8, 1.2)
        
#         self.result_ready.emit(self.lens, result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Création des widgets
    multi_power = MultiPowerSupplyWidget()
    calculations = CalculationsWidget(multi_power_supply=multi_power)
    
    # Affichage
    multi_power.show()
    calculations.show()
    
    sys.exit(app.exec())

