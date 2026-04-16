import classe_lentille
import rayon
import initialisation
import matplotlib.pyplot as plt
import numpy as np

#création des lentilles
L1=classe_lentille.lentille('condenseur1',b=0.07487,a=0.001)
L2=classe_lentille.lentille('condenseur2',b=0.16437,a=0.0005)
L3=classe_lentille.lentille('condenseur3',b=0.39287,a=0.0065)

#position de l'écran
zmax=0.47287

#énergie du faisceau en eV
phi=5000

#condition initiale du rayon (champ de vue, ouverture)
CI=[0,1]

#initialisation de toutes les variables qui n'ont besoin d'être calculées une seule fois. pour éviter de devoir tout recalculer à chaque fois (+ rapide)
L1,L2,L3,psi1,psi2,psi3,z=initialisation.initialisation(L1,L2,L3,zmax)

while True:
    I=[0.1886,0.0707,1.10818]
    (u,B)=rayon.rayon(L1,L2,L3,psi1,psi2,psi3,CI,I,phi)
    plt.figure()
    plt.plot(z,B,color='grey',linestyle='--')
    plt.plot(z,u,color='blue')
    plt.show()



