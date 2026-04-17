import numpy as np

def initialisation(L1,L2,L3,zmax):
    
    z=np.arange(0,zmax,0.0005)
    
    z_inter1=L1.b+(L2.b-L1.b)/2
    z_inter2=L2.b+(L3.b-L2.b)/2
    
    mask1=(z>=0)&(z<z_inter1)
    mask2=(z>=z_inter1)&(z<z_inter2)
    mask3=(z>=z_inter2)&(z<=zmax)
    
    L1.z=z[mask1]
    L2.z=z[mask2]
    L3.z=z[mask3]
    
    psi1 = np.pi/2 - np.arctan((L1.z - L1.b)/L1.a)
    psi2 = np.pi/2 - np.arctan((L2.z - L2.b)/L2.a)
    psi3 = np.pi/2 - np.arctan((L3.z - L3.b)/L3.a)
    
    return L1,L2,L3,psi1,psi2,psi3,z