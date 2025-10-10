import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6 import uic
from power_supply import PowerSupply
from camera_widget_stand_alone import CameraWidget
from multi_power_supply_stand_alone import MultiPowerSupplyWidget
from scan_widget_stand_alone import ScanWidget
from settings_stand_alone import SettingsWidget
from PyQt6.QtCore import Qt

# Chemin vers le fichier UI
dossier_courant = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(dossier_courant,"interface","main_window.ui")
if not os.path.exists(ui_file):
    raise FileNotFoundError(f"UI introuvable : {ui_file}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(ui_file, self)  # Charge les widgets promus automatiquement

        self.pushButton_multi_power_supply.clicked.connect(self.open_power_supply)
        self.pushButton_camera.clicked.connect(self.open_camera)
        self.pushButton_scan.clicked.connect(self.open_scan)

        self.checkBox_admin.stateChanged.connect(self.toggle_admin_mode)
        #self.pushButton_settings.clicked.connect(self.open_settings)
        #self.pushButton_settings.setVisible(False)
        self.lineEdit_password.setVisible(False)
        self.lineEdit_password.textChanged.connect(self.check_password)


        # Garde une référence aux fenetres pour éviter la destruction prématurée
        self.camera_window = None
        self.scan_window = None
        self.power_supply_window = None

    def open_camera(self):
        print("Camera")
        if self.camera_window is None:
            self.camera_window = CameraWidget()
            self.camera_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Libérer la mémoire à la fermeture
            self.camera_window.destroyed.connect(self.on_camera_closed)
        self.camera_window.show()
        self.camera_window.raise_()
        self.camera_window.activateWindow()

    def on_camera_closed(self):
        self.camera_window = None


    def open_power_supply(self):
        print("power")
        if self.power_supply_window is None:
            self.power_supply_window = MultiPowerSupplyWidget()
            self.power_supply_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Libérer la mémoire à la fermeture
            self.power_supply_window.destroyed.connect(self.on_power_supply_closed)
        self.power_supply_window.show()
        self.power_supply_window.raise_()
        self.power_supply_window.activateWindow()

    def on_power_supply_closed(self):
        self.power_supply_window = None


    def open_scan(self):
        print("scan")
        self.on_camera_closed()
        #self.on_power_supply_closed()

        #self.pushButton_settings.setEnabled(False)
        self.pushButton_camera.setEnabled(False)
        #self.pushButton_multi_power_supply.setEnabled(False)
        self.checkBox_admin.setEnabled(False)


        if self.scan_window is None:
            self.scan_window = ScanWidget()
            self.scan_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Libérer la mémoire à la fermeture
            self.scan_window.destroyed.connect(self.on_scan_closed)
        self.scan_window.show()
        self.scan_window.raise_()
        self.scan_window.activateWindow()

    
        



    def on_scan_closed(self):
        self.scan_window = None

        #self.pushButton_settings.setEnabled(True)
        self.pushButton_camera.setEnabled(True)
        self.pushButton_multi_power_supply.setEnabled(True)
        self.checkBox_admin.setEnabled(True)


    def toggle_admin_mode(self, state):
        """Active/désactive le mode admin"""
        if state == Qt.CheckState.Checked.value:
            # Afficher le champ mot de passe
            self.lineEdit_password.setVisible(True)
            self.lineEdit_password.setFocus()
        else:
            self.lineEdit_password.setVisible(False)
            #self.pushButton_settings.setVisible(False)
            self.lineEdit_password.clear()

    def check_password(self, text):
        """Vérifie le mot de passe et active le bouton settings si correct"""
        # Mot de passe exemple - à remplacer par votre logique
        correct_password = "opc" 
        if text == correct_password:
            self.open_settings() 
      
    def open_settings(self):
        """Ouvre la fenêtre de configuration"""
            
        self.settings_widget = SettingsWidget()  # Crée une nouvelle instance à chaque clic
        self.settings_widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.settings_widget.show()
        self.settings_widget.raise_()
        self.settings_widget.activateWindow()
        self.settings_widget.activateWindow()  # Pour donner le focus
    

    def closeEvent(self, event):
        print("Fermeture de l'application - désactivation des alimentations")
        
       
        # Fermer les fenêtres enfants
        if self.power_supply_window:
            self.power_supply_window.close()
        if self.scan_window:
            self.scan_window.close()
        if self.camera_window:
            self.camera_window.close()
            
        event.accept()
        print("Close")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())