import sys
import numpy as np
from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
from scan import ScanGenerator
from acq import NiDetectorAcquisition
from power_supply import PowerSupply


class AcquisitionWorker(QtCore.QObject):
    pixel_acquired = QtCore.pyqtSignal(int, int, float)
    finished = QtCore.pyqtSignal()


    def __init__(self, scan: ScanGenerator, alim: PowerSupply,
                 channel_x: int, channel_y: int,
                 acquisition: NiDetectorAcquisition):
        super().__init__()
        self.scan = scan
        self.alim = alim
        self.channel_x = channel_x
        self.channel_y = channel_y
        self.acquisition = acquisition
        self._running = True

        self.resolution = self.scan.resolution
        self.samples_per_pixel = self.scan.samples_per_pixel
        self.total_pixels = self.resolution * self.resolution
        self.x_array = self.scan.get_x()
        self.y_array = self.scan.get_y()

    def stop(self):
        #self._running = False
        """Demande l’arrêt du scan et met les courants à zéro."""
        self._running = False
        # Mettre les courants à zéro immédiatement
        self.alim.set_current(0, channel=self.channel_x)
        self.alim.set_current(0, channel=self.channel_y)
        # Optionnel : mettre aussi les tensions à zéro si nécessaire
        self.alim.set_voltage(0, channel=self.channel_x)
        self.alim.set_voltage(0, channel=self.channel_y)

    def run(self):
        sample_index = 0
        for i_pixel in range(self.total_pixels):
            if not self._running:
                break

            i_start = sample_index
            i_end = i_start + self.samples_per_pixel
            if i_end > len(self.x_array):
                break

            gray_values = []
            for idx in range(i_start, i_end):
                if not self._running:
                    break
                x = self.x_array[idx]
                y = self.y_array[idx]

                self.alim.set_current(x, channel=self.channel_x)
                self.alim.set_current(y, channel=self.channel_y)
                gray = self.acquisition.read_gray_level()
                gray_values.append(gray)

            if not self._running:
                break

            mean_gray = sum(gray_values) / len(gray_values)
            row = i_pixel // self.resolution
            col = i_pixel % self.resolution
            self.pixel_acquired.emit(row, col, mean_gray)
            sample_index += self.samples_per_pixel

        self.finished.emit()


class SEMImageLive(QtWidgets.QMainWindow):
    """
    Cet objet sert uniquement à piloter le ImageView que l'on lui donne.
    S'il reçoit 'image_view' (un pg.ImageView), il n'appelle PAS setCentralWidget,
    sinon il en crée un nouveau et le place dans sa propre fenêtre.
    """
    scan_completed = QtCore.pyqtSignal()
    def __init__(self, scan: ScanGenerator, alim: PowerSupply,
                 channel_x: int, channel_y: int,
                 acquisition: NiDetectorAcquisition,
                 image_view: pg.ImageView = None):
        super().__init__()
        self.setWindowTitle("SEM Image Live Viewer")

        # Si on n'a pas passé de ImageView, en créer un et l'afficher dans cette fenêtre
        if image_view is None:
            self.image_view = pg.ImageView()
            self.setCentralWidget(self.image_view)
        else:
            # On reçoit un ImageView existant (par ex. depuis ScanWidget),
            # on ne fait pas setCentralWidget(image_view) pour ne pas casser le layout parent.
            self.image_view = image_view

        self.scan = scan
        self.alim = alim
        self.channel_x = channel_x
        self.channel_y = channel_y
        self.acquisition = acquisition

        self.resolution = self.scan.resolution
        self.samples_per_pixel = self.scan.samples_per_pixel
        self.total_pixels = self.resolution * self.resolution

        # Image  initiale (tout noir)
        self.image = np.zeros((self.resolution, self.resolution), dtype=np.uint8)
        # Si le ImageView existait (dans ScanWidget), il affichait déjà quelque chose à l'init.
        # Sinon, on vient de créer un nouveau ImageView ci-dessus :
        self.image_view.setImage(self.image.T, autoLevels=True)

        self.worker = None
        self.thread = None

        # Si on est en mode “fenêtre seule”, on propose des boutons Start/Stop.
        if image_view is None:
            button_layout = QtWidgets.QHBoxLayout()
            self.stop_button.setEnabled(False)
            button_layout.addWidget(self.start_button)
            button_layout.addWidget(self.stop_button)

            container = QtWidgets.QWidget()
            v_layout = QtWidgets.QVBoxLayout()
            v_layout.addWidget(self.image_view)
            v_layout.addLayout(button_layout)
            container.setLayout(v_layout)
            self.setCentralWidget(container)

    

    def start(self):
        """Démarre l’acquisition dans un QThread."""
        # Si un worker existait déjà, on l’arrête
   
        if self.thread is not None:
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
            self.thread = None
    
        if self.worker is not None:
            self.worker = None

        # Remise à zéro de l’image
        self.image[:] = 0
        # AutoLevels True une fois pour recalculer les contrastes sur le 1er affichage
        self.image_view.setImage(self.image.T, autoLevels=True)

        # Regénérer le scan XY
        self.scan.generate()

        # Créer worker et thread
        self.worker = AcquisitionWorker(
            scan=self.scan,
            alim=self.alim,
            channel_x=self.channel_x,
            channel_y=self.channel_y,
            acquisition=self.acquisition
        )
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)

        self.worker.pixel_acquired.connect(self.update_image)
        self.worker.finished.connect(self.on_finished)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)



        self.thread.start()

    def update_image(self, row: int, col: int, gray_value: float):
        """Met à jour la valeur d’un pixel et rafraîchit l’affichage."""
        self.image[row, col] = gray_value
        self.image_view.imageItem.setImage(self.image.T, autoLevels=True)

    def stop(self):
        """Demande l’arrêt au worker et met à jour l’état des boutons."""
        
        if self.worker is not None:
            self.worker.stop()

        if self.thread is not None:
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()

   

    def on_finished(self):
        """Exécuté quand le worker a émis `finished`."""
        # S'assurer que les courants sont bien à zéro
        self.alim.set_current(0, channel=self.channel_x)
        self.alim.set_current(0, channel=self.channel_y)
        # Optionnel : mettre aussi les tensions à zéro si nécessaire
        self.alim.set_voltage(0, channel=self.channel_x)
        self.alim.set_voltage(0, channel=self.channel_y)
        self.scan_completed.emit()
        print("Scan terminé ou arrêté.")


