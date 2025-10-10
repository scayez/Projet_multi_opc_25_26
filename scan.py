import numpy as np
from typing import Tuple

class ScanGenerator:
    """
    Génère les signaux de commande X et Y pour un balayage raster 2D
    (comme dans un microscope électronique à balayage ou un oscilloscope XY).

    Attributs :
        min_current (float) : Valeur minimale du courant de consigne.
        max_current (float) : Valeur maximale du courant de consigne.
        resolution (int) : Nombre de pixels par ligne et par colonne.
        samples_per_pixel (int) : Nombre d’échantillons à collecter pour chaque pixel.
        duration (float) : Durée totale du scan en secondes.
        sample_rate (float) : Taux d’échantillonnage en Hz.
        time_array (np.ndarray) : Tableau des temps associé aux signaux.
        x_signal (np.ndarray) : Signal de balayage en X (courant).
        y_signal (np.ndarray) : Signal de balayage en Y (courant).
    """
    def __init__(
        self,
        current_range: Tuple[float, float],  # (min_current, max_current)
        resolution: int,                     # nombre de pixels (même pour h et v)
        samples_per_pixel: int,             # nombre d’échantillons par pixel
        ):

        """
        Initialise le générateur de balayage.

        Args:
            current_range (Tuple[float, float]): Plage de courant (min, max) pour X et Y.
            resolution (int): Nombre de pixels par ligne et colonne (image carrée).
            samples_per_pixel (int): Nombre d'échantillons à collecter par pixel.
        """
        self.min_current, self.max_current = current_range
        self.resolution = resolution
        self.samples_per_pixel = samples_per_pixel
        self.time_array = None
        self.x_signal = None
        self.y_signal = None

    def generate(self):
        """
        Génère les signaux de balayage X et Y pour un scan complet.

        Le balayage suit un motif raster (ligne par ligne). Chaque ligne horizontale
        est scannée de gauche à droite, et la position verticale change ensuite.

        Les signaux sont stockés dans `self.x_signal` et `self.y_signal`.
        """
        # Génération X (balayage horizontal)
        single_line = np.repeat(
            np.linspace(self.min_current, self.max_current, self.resolution),
            self.samples_per_pixel
        )
        self.x_signal = np.tile(single_line, self.resolution)
        
        # Génération Y (balayage vertical)
        self.y_signal = np.repeat(
            np.linspace(self.min_current, self.max_current, self.resolution),
            self.samples_per_pixel * self.resolution
        )

    def generate_horizontal_scan(self):
        """
        Génère un signal de balayage horizontal répété pour chaque ligne.
        Returns:
            np.ndarray: Signal X sous forme d’un tableau de courant.
        """
        single_line = np.repeat(
            np.linspace(self.min_current, self.max_current, self.resolution),
            self.samples_per_pixel
        )
        return np.tile(single_line, self.resolution)

    def generate_vertical_scan(self):
        """
        Génère un signal en escalier correspondant à la position verticale,
        maintenu constant pendant toute la durée d'une ligne horizontale.
        Returns:
            np.ndarray: Signal Y sous forme d’un tableau de courant.
        """
        return np.repeat(
            np.linspace(self.min_current, self.max_current, self.resolution),
            self.samples_per_pixel * self.resolution
        )
    # #Accès aux signaux générés par generate
    # def get_time(self):
    #     """
    #     Retourne le vecteur temporel associé au scan.
    #     Returns:
    #         np.ndarray: Vecteur des temps (en secondes).
    #     """
    #     return self.time_array

    def get_x(self):
        """
        Retourne le signal de balayage X.
        Returns:
            np.ndarray: Signal X (courant) généré par `generate()`.
        """
        return self.x_signal

    def get_y(self):
        """
        Retourne le signal de balayage Y.
        Returns:
            np.ndarray: Signal Y (courant) généré par `generate()`.
        """
        return self.y_signal

