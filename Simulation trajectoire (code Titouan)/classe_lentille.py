import numpy as np
import matplotlib.pyplot as plt

class lentille:
    # phi : énergie du faisceau en eV
    # b : position de la lentille sur l'axe de propagation en mètres
    # B0 : hauteur du champ de Glaser
    # a : largeur du champ
    # z : l'intervalle sur lequel on conidère que la lentille a de l'influence
    # CI : condition initiale de hauteur et d'angle à l'entrée de la lentille
    def __init__(self,id=None,b=None,B0=None,a=None,z=None,psi=None):
        self.id=id
        self.b=b
        self.B0=B0
        self.a=a
        self.z=z
        self.psi=psi
    
    def w(self,phi):
        return np.sqrt(1+(2.965*10**5)**2*self.B0**2*self.a**2/(4*phi))
    
    def alpha(self,psi,phi):
        return psi[0] - (1/self.w(phi)*np.arctan(self.w(phi)*np.tan(psi[0])))
    
    def B(self,z):
        return self.B0/(1+((z-self.b)/self.a)**2)
    
    def rayon(self,CI,psi,phi):
        w=self.w(phi)
        alpha=self.alpha(psi,phi)
        principal=np.sin(psi[0])*np.sin(w*(psi-alpha))/(np.sin(psi)*np.sin(w*(psi[0]-alpha)))
        marginal=(-1)*self.a*np.sin(w*(psi-psi[0]))/(w*np.sin(psi[0])*np.sin(psi))
        return CI[0]*principal+CI[1]*marginal
    
    