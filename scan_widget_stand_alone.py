import os
import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QButtonGroup, QFileDialog
from PyQt6 import uic
from pyqtgraph import ImageView
from image_viewer import SEMImageLive 
from scan import ScanGenerator
from power_supply import PowerSupply
from acq import NiDetectorAcquisition
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import pyqtSlot

# Définir le chemin du fichier UI (interface graphique)
dossier_courant = os.path.dirname(os.path.abspath(__file__))
qtCreatorFile = os.path.join(dossier_courant, "interface", "scan.ui")
# Vérification de l'existence du fichier d'interface
if not os.path.exists(qtCreatorFile):
    raise FileNotFoundError(f"Fichier UI introuvable : {qtCreatorFile}")

class ScanWidget(QWidget):
    """
    Widget principal pour la gestion d'un scan SEM contrôlé par une alimentation.
    Ce widget permet de configurer les paramètres de scan, de démarrer/arrêter 
    l'acquisition, et d'afficher les données en direct.

    Attributs :
        alim : instance de PowerSupply pour le contrôle de l'alimentation.
        acquisition : instance de NiDetectorAcquisition pour l'acquisition des niveaux de gris sur le detecteur.
        sem_viewer : instance de SEMImageLive pour l'acquisition et l'affichage de l'image.
    """
    def __init__(self, parent=None):
        """
        Initialise l'interface graphique et les périphériques nécessaires.
        """
        super().__init__(parent)
        uic.loadUi(qtCreatorFile, self)  # Charger l'UI
        # Connexion des boutons de contrôle
        self.pushButton_start.clicked.connect(self.start_scan)
        self.pushButton_stop.clicked.connect(self.stop_scan)
        self.pushButton_save.clicked.connect(self.save_image)
    
        # Initialisation de l'alimentation
        self.adresse_alim__GPP2323 = "ASRL5::INSTR"
        self.alim = PowerSupply(
            connection_mode="USB",
            address=self.adresse_alim__GPP2323,
            baud_rate=115200,
            Vmin=0, Vmax=12000,
            Imin=0.0, Imax=1000 #ATTENTION CETTE VALEUR SERT DE SECURITE. Elle est prioritaire sur doubleSpinBox_currrent_range
        )
        # Vérification de la connexion à l'alimentation
        if self.alim.open_connection() is None:
            raise RuntimeError("Connexion à l'alim échouée !")
        # Activer les sorties 1 et 2
        self.alim.enable_output(channel=1)
        self.alim.enable_output(channel=2)
        # Initialiser l'acquisition simulée #####ATTENTION CHANGER POUR ACQUISITION REELE ######
        #self.acquisition = NiDetectorAcquisition(response_time=0.001)
        self.acquisition = NiDetectorAcquisition(channel_read="Dev2/ai1")#, response_time=0.001)
        self.acquisition.voltageMeasured.connect(self.update_voltage_label)  # Ajoute cette ligne
        self.sem_viewer = None
        # Désactiver certains éléments de l'interface tant qu'aucun scan n'est lancé
        self.update_ui_state(scanning=False)

    # Afficher la tension SE en continu dans l'interface graphique
    @pyqtSlot(float)
    def update_voltage_label(self, voltage):
        self.label_voltage_measured.setText(f"{voltage:.6f}")

    def start_scan(self):
        """
        Démarre le processus de scan en initialisant les paramètres,
        créant le scan et le viewer, puis en lançant l'acquisition.
        """
        # Arrêter un scan précédent s’il existe
        if self.sem_viewer is not None:
            self.stop_scan()  # Arrête un éventuel scan en cours
        # Désactiver les contrôles de l’interface
        self.update_ui_state(scanning=True)

        # Régler la tension limite AVANT le scan (adapter la valeur à votre expérience) !! YANIS ET ROMAIN
        self.alim.set_voltage(0.7, channel=1)  # 10V par exemple
        self.alim.set_voltage(0.7, channel=2)


        # Lire les paramètres depuis l'interface utilisateur
        current_max = self.doubleSpinBox_currrent_range.value()/1000  # suppose que le min est toujours 0 .  mA → A
        self.current_range = (0, current_max)

        self.resolution = self.spinBox_reso.value()
        self.samples_per_pixel = self.spinBox_sample_per_pix.value()

        # Calculer la durée du scan

        print(f"Plage courant : {self.current_range}")
        print(f"Résolution : {self.resolution}")
        print(f"Samples/pixel : {self.samples_per_pixel}")

        # Créer un objet de scan avec les paramètres
        scan = ScanGenerator(
            current_range=self.current_range,
            resolution=self.resolution,
            samples_per_pixel=self.samples_per_pixel,
            )
        scan.generate()

        # Créer le viewer SEM (acquisition + affichage)
        self.sem_viewer = SEMImageLive(
            scan=scan,
            alim=self.alim,
            channel_x=1,
            channel_y=2,
            acquisition=self.acquisition,
            image_view=self.image_view
        )
        # Connexion du signal de fin de scan
        self.sem_viewer.scan_completed.connect(self.handle_scan_finished)#signal envoyé par SEM_ImageLive
        self.sem_viewer.start()

    def stop_scan(self):
        """
        Stoppe le scan en cours si un viewer est actif.
        """
        try:
            if self.sem_viewer is not None:
                self.sem_viewer.stop()
        except Exception as e:
            print(f"Erreur lors de l'arrêt du scan : {e}")

    def handle_scan_finished(self):
        """
        Slot appelé à la fin du scan (signal depuis SEMImageLive).
        Réactive les contrôles dans l’interface.
        """
        self.update_ui_state(scanning=False)
        print("Scan terminé (signal reçu)")
      
    def update_ui_state(self, scanning: bool):
        """
        Active ou désactive les éléments de l'interface selon l'état du scan.
        
        Args:
            scanning (bool): True si un scan est en cours, False sinon.
        """
        self.doubleSpinBox_currrent_range.setEnabled(not scanning)
        self.spinBox_reso.setEnabled(not scanning)
        self.spinBox_sample_per_pix.setEnabled(not scanning)
        self.pushButton_start.setEnabled(not scanning)
        self.pushButton_stop.setEnabled(scanning)
        self.pushButton_save.setEnabled(not scanning and self.sem_viewer is not None and self.sem_viewer.image is not None)

    # Enregistrer l'image actuelle dans un fichier
    def save_image(self):
        """
        Enregistre l'image actuelle dans un fichier PNG.
        Ouvre une boîte de dialogue pour choisir l'emplacement et le nom du fichier.
        """
        if self.sem_viewer is None or self.sem_viewer.image is None:
            print("Aucune image à enregistrer. Lancez d'abord un scan.")
            return

        # Ouvrir une boîte de dialogue pour choisir le fichier
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'image",
            "",
            "Images PNG (*.png);;Images TIFF (*.tiff);;Tous les fichiers (*)"
        )

        if file_path:
            try:
                import numpy as np
                from PIL import Image
                # Convertir le tableau numpy en image PIL
                img_data = self.sem_viewer.image
                # Assurer que les valeurs sont dans la plage correcte
                if img_data.dtype != np.uint8:
                    img_data = (img_data / img_data.max() * 255).astype(np.uint8) if img_data.max() > 0 else img_data.astype(np.uint8)
                img = Image.fromarray(img_data)
                img.save(file_path)
                print(f"Image enregistrée : {file_path}")
            except Exception as e:
                print(f"Erreur lors de l'enregistrement : {e}")

    def closeEvent(self, event):
        """
        Gestion de la fermeture de la fenêtre : arrête le scan proprement.
        """
        self.stop_scan()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScanWidget()
    window.show()
    sys.exit(app.exec())