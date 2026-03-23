import sys
import os
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QRect
from PyQt6.QtWidgets import QApplication, QWidget, QButtonGroup
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QFileDialog
import cv2

# Charger dynamiquement le fichier .ui
dossier_courant = os.path.dirname(os.path.abspath(__file__))
qtCreatorFile = os.path.join(dossier_courant, "interface", "camera.ui")


class CameraWidget(QWidget):
    """
    Widget PyQt6 pour afficher un flux vidéo de la webcam, avec possibilité de zoom,
    de déplacement dans l'image, et de capture manuelle.

    Gère un thread séparé (VideoThread) pour capturer les images en continu
    sans bloquer l'interface graphique.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(qtCreatorFile, self)  # Charger l'UI

        # Initialisation de la vue et du zoom
        self.zoom_level = 1.0
        self.view_position = [0, 0]  # Position de la vue 
        self.view_size = (640, 480)  # Taille fixe de l'affichage 

        # Préparer le QLabel pour afficher les images
        self.label_camera.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Afficher un message de chargement
        self.label_camera.setText("Camera loading...")  # Afficher un message de chargement
        self.label_camera.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrer le texte
        self.label_camera.setFixedSize(self.view_size[0], self.view_size[1])  # Taille fixe
        self.label_camera.setFocus() # Important pour capter les événements clavier

        # Désactiver la gestion de la taille par le layout
        #self.label_camera.setFixedSize(self.view_size[0], self.view_size[1])  # Taille fixe

        # Assurer que le QLabel a le focus
        #self.label_camera.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permettre au label de recevoir le focus ###########
        #self.label_camera.setFocus()  # Donner le focus au label ###########
         # Créer et démarrer le thread de capture vidéo
        # Création et démarrage du thread vidéo
        self.video_thread = VideoThread()
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()

        # Connexion du bouton de capture à la méthode dédiée
        self.pushButton_capture.clicked.connect(self.capture_image)


    def update_image(self, q_img):
        """
        Met à jour l'affichage avec une nouvelle image issue du thread caméra.

        Args:
            q_img (QImage): Image capturée, transmise par signal depuis VideoThread.
        """
        # Calculer la zone visible de l'image en fonction du zoom
        zoomed_width = int(q_img.width() * self.zoom_level)
        zoomed_height = int(q_img.height() * self.zoom_level)
        zoomed_img = q_img.scaled(zoomed_width, zoomed_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)  # Optimisation ###########

        # Calculer la zone visible de l'image zoomée
        view_rect = QRect(self.view_position[0], self.view_position[1], self.view_size[0], self.view_size[1])
        visible_img = zoomed_img.copy(view_rect)

        # Mettre à jour l'image dans le QLabel
        self.label_camera.setPixmap(QPixmap.fromImage(visible_img))
        self.label_camera.setFixedSize(self.view_size[0], self.view_size[1])  # Taille fixe


    def keyPressEvent(self, event):
        """
        Gère les événements clavier pour le zoom (+/-) et la navigation dans l'image.

        Utilise les flèches pour se déplacer dans l'image zoomée.
        """
        if event.key() == Qt.Key.Key_Plus:
            self.zoom_level *= 1.1  # Augmenter le zoom de 10%
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_level *= 0.9  # Diminuer le zoom de 10%
        elif event.key() == Qt.Key.Key_Left:
            self.view_position[0] = max(0, self.view_position[0] - 10)  # Déplacer vers la gauche 
        elif event.key() == Qt.Key.Key_Right:
            self.view_position[0] += 10  # Déplacer vers la droite 
        elif event.key() == Qt.Key.Key_Up:
            self.view_position[1] = max(0, self.view_position[1] - 10)  # Déplacer vers le haut
        elif event.key() == Qt.Key.Key_Down:
            self.view_position[1] += 10  # Déplacer vers le bas

        # Mettre à jour l'image avec le nouveau niveau de zoom et la position de la vue
        self.update_image(self.video_thread.current_frame)

    def capture_image(self):
        """
        Capture l'image actuellement affichée et propose de la sauvegarder.

        Les signaux du thread sont temporairement bloqués pour éviter d’écraser
        l’image pendant l’ouverture de la boîte de dialogue.
        """
        pixmap = self.label_camera.pixmap()
        if pixmap and not pixmap.isNull():  # Vérifier que le QLabel contient bien une image
            # Bloquer temporairement les signaux du thread pour éviter qu'il ne mette à jour le label pendant la capture ### 
            self.video_thread.blockSignals(True)
           # Ouvrir une boîte de dialogue pour choisir l'emplacement de sauvegarde
            file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder l'image", 
                                                   os.path.join(dossier_courant, "capture.png"),
                                                   "Images (*.png *.jpg *.bmp)") 
             # Réactiver les signaux du thread après la fermeture de la boîte de dialogue ### 
            self.video_thread.blockSignals(False)                                    
        if file_path:  # Vérifier si l'utilisateur a validé la sauvegarde
            pixmap.save(file_path)  ###
            print(f"Image capturée et enregistrée sous {file_path}") 
        else:
            print("Aucune image disponible pour la capture.")  

   
  
    def closeEvent(self, event):
        """
        Événement déclenché lors de la fermeture de la fenêtre.

        Permet de s'assurer que le thread de capture est correctement arrêté
        pour éviter les fuites de mémoire ou les blocages de périphérique.
        """
        self.video_thread.stop()
        event.accept()

class VideoThread(QThread):
    """
    Thread de capture vidéo pour lire les images en continu depuis la webcam.

    Utilise un signal `change_pixmap_signal` pour transmettre les images
    à l’interface principale sans bloquer l'UI.
    """
    # Signal pour envoyer l'image capturée à l'interface
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.current_frame = None

    def run(self):
        # Capturer la vidéo depuis la webcam
 
        self.cap = cv2.VideoCapture(0)
  
        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                # Convertir l'image OpenCV (BGR) en QImage (RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.current_frame = q_img  # Stocker l'image actuelle
                # Envoyer l'image à l'interface via le signal
                self.change_pixmap_signal.emit(q_img)

        # Libérer la webcam lorsque le thread est arrêté
        self.cap.release()

    def stop(self):
        """Arrêter le thread proprement."""
        self._run_flag = False
        self.wait()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = CameraWidget()
    window.show()
    sys.exit(app.exec())
