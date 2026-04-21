import classe_lentille
import rayon
import initialisation
import matplotlib.pyplot as plt
import numpy as np

class simulation:
    def __init__(self,L1,L2,L3,psi1,psi2,psi3,z,zmax,phi,champ_de_vue,ouverture):
        self.L1=L1
        self.L2=L2
        self.L3=L3
        self.psi1=psi1
        self.psi2=psi2
        self.psi3=psi3
        self.z=z
        self.zmax=zmax         #position de l'écran
        self.phi=phi        #énergie du faisceau en eV
        self.champ_de_vue=champ_de_vue
        self.ouverture=ouverture



    def Init_Simu(self):
        #création des lentilles
        self.L1=classe_lentille.lentille('condenseur1',b=0.07487,a=0.001)
        self.L2=classe_lentille.lentille('condenseur2',b=0.16437,a=0.0005)
        self.L3=classe_lentille.lentille('condenseur3',b=0.39287,a=0.0065)

        #condition initiale du rayon (champ de vue, ouverture)
        self.CI=[self.champ_de_vue,self.ouverture]

        #initialisation de toutes les variables qui n'ont besoin d'être calculées une seule fois. pour éviter de devoir tout recalculer à chaque fois (+ rapide)
        L1,L2,L3,self.psi1,self.psi2,self.psi3,self.z=initialisation.initialisation(L1,L2,L3,self.zmax)
        return self.z
    

    def simu(self,Icond1,Icond2,Iobj):
        I=[Icond1,Icond2,Iobj]
        (u,B)=rayon.rayon(self.L1,self.L2,self.L3,self.psi1,self.psi2,self.psi3,self.CI,I,self.phi)
        return u,B


