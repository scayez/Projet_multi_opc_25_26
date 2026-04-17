import initialisation
import numpy as np
import matplotlib.pyplot as plt

#cette fonction prend en entrée les trois lentilles de la colonne sem, la position de l'écran, le courant dans les bobines ainsi que les conditions initiales du rayon
#elle renvoie une modélisation du champ magnétique créé par chaque bobine ainsi que la trajectoire du rayon le long de la colonne

def rayon(L1,L2,L3,psi1,psi2,psi3,CI,I,phi):
    
    coef=[0.25509,0.736987,0.019275]
    
    L1.B0=I[0]*coef[0]
    L2.B0=I[1]*coef[1]
    L3.B0=I[2]*coef[2]
    
    u1=L1.rayon(CI,psi1,phi)
    du1_dz=(u1[-1]-u1[-2])/(L1.z[-1]-L1.z[-2])
    
    u2=L2.rayon([u1[-1],du1_dz],psi2,phi)
    du2_dz=(u2[-1]-u2[-2])/(L2.z[-1]-L2.z[-2])
    
    u3=L3.rayon([u2[-1],du2_dz],psi3,phi)
    
    u=np.concatenate((u1,u2,u3))
    
    B=np.concatenate((L1.B(L1.z),L2.B(L2.z),L3.B(L3.z)))
    
    return u,B

