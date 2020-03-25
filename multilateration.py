import numpy as np

v = 299702547 #speed of light in air (meters/second)
dim = 3 # number of dimensions we are solving for



''' Calculates the time difference of a wavefront touching two receivers given the wavefront's speed
Ta: time of arrival at receiver A
Tb: time of arrival at receiver B
vel: speed of wavefront (default v)
Returns vTm (v*Ta - v*Tb)'''
def GetVTM(Ta, Tb, vel = v):
    return vel * (Ta - Tb)

''' Calculates one of the first three coefficients in Ax + By + Cz + D = 0
Pm, P1,: (Axis coordinate of receivers M & 1 -- must be the same axis)
    P = X-coord -> returns Am
    P = Y-coord -> returns Bm
    P = Z-coord -> returns Cm
Tm, T1, T0: (signal's time of arrival @ receiver M, 1, & 0 respectively)'''
def GetCoeffABC(Pm, P1, Tm, T1, T0):
    vtM = GetVTM(Tm,T0)
    vt1 = GetVTM(T1,T0)
    return 2 * (Pm/vtM - P1/vt1)

''' Calculates D in Ax + By + Cz + D = 0
Xm, Ym, Zm: (X/Y/Z coordinates of receiver M, respectively)
X1, Y1, Z1: (X/Y/Z coordinates of receiver 1, respectively)
Tm, T1, T0: (signal time of arrival @ receivers M, 1, 0 respectively)'''
def GetCoeffD(Xm, Ym, Zm, X1, Y1, Z1, Tm, T1, T0):
    vtM = GetVTM(Tm,T0)
    vt1 = GetVTM(T1,T0)
    chunk1 = (X1**2 + Y1**2 + Z1**2)/vt1
    chunkM = (Xm**2 + Ym**2 + Zm**2)/vtM
    return vtM - vt1 - chunkM + chunk1

''' Returns a tuple of the 4 coefficients in Ax + By + Cz + D = 0
Xm, Ym, Zm: (X/Y/Z coordinates of receiver M, respectively)
X1, Y1, Z1: (X/Y/Z coordinates of receiver 1, respectively)
Tm, T1, T0: (signal time of arrival @ receivers M, 1, 0 respectively)'''
def GetXYZEquations(Xm, Ym, Zm, X1, Y1, Z1, Tm, T1, T0):
    A = GetCoeffABC(Xm, X1, Tm, T1, T0)
    B = GetCoeffABC(Ym, Y1, Tm, T1, T0)
    C = GetCoeffABC(Zm, Z1, Tm, T1, T0)
    D = GetCoeffD(Xm, Ym, Zm, X1, Y1, Z1, Tm, T1, T0)
    return (A,B,C,D)

'''

'''
def LocateTag(*args):
    # Make a list of the timestamps
    timestamps = list(args)

    # Create an empty array of size: (timestamps - 2) x 4 
    # [One column for each coefficient]
    a = np.empty([len(timestamps)-2,dim+1])
    # Create an array of zeros
    b = np.zeros([len(timestamps)-2,1])

    # For each timestamp from the 2nd to the last
    for stamp in timestamps[2:]:
        # Use GetXYZEquations to generate the coefficients as a tuple

