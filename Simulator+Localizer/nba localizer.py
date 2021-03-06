import time
import math
import pprint
import numpy as np
import scipy.optimize as spo
from filterpy.kalman import ExtendedKalmanFilter
from filterpy.common import Q_discrete_white_noise
import sympy
import matplotlib.pyplot as plt
import random
import csv
import os
import sys
from basketball_mapping import *
pp = pprint.PrettyPrinter()
pprint = pp.pprint

##TEST SIMULATION PARAMETERS#########
WITH_NOISE = True
NOISE_STD_DEV = 1.5 #nanoseconds
ANCHOR_COUNT = 6 # max of 6
MAX_SAMPLE_COUNT = 500 # None if you want to process whole file
CALIBRATION_SAMPLES = 100
ANCHORS = [(0,0), (0, footToMeter(COURT_HEIGHT_FEET)),
            (footToMeter(COURT_WIDTH_FEET), 0), (footToMeter(COURT_WIDTH_FEET), footToMeter(COURT_HEIGHT_FEET)),
            (footToMeter(COURT_WIDTH_FEET//2), 0), (footToMeter(COURT_WIDTH_FEET//2), footToMeter(COURT_HEIGHT_FEET))][:ANCHOR_COUNT]
WITH_SMOOTHING = False
SMOOTHING_FACTOR = 1.45
P = 100
R = 10000
Q = 1000
WITH_CMA = True
CMA_WINDOW_SIZE = 7 if ANCHOR_COUNT==4 else 5
LINEAR_ON = False
HYPERBOLA_ON = False
VELOCITY = True
#######################################
realColor = 'black'
linColor = 'purple'
hypColor = 'green'
filterColor = 'blue'
#######################################
SAMPLE_IDX = 'Sample_idx'
TIME = 'timestamp_ms'
GAME_TIME = "adjusted_game_time"
PLAYER_ID = "player_id"
REAL_X = "realX"
REAL_Y = "realY"
in_headers = [SAMPLE_IDX, TIME, GAME_TIME, PLAYER_ID, REAL_X, REAL_Y]
out_headers = [SAMPLE_IDX, TIME, GAME_TIME, PLAYER_ID, REAL_X, REAL_Y, "velX", "velY", "linEstX", "linEstY", "hypEstX", "hypEstY", "filtEstX", "filtEstY", "linErr", "hypErr", "filtErr", "linRMSE", "hypRMSE", "filtRMSE"]

def generateTestDesc():
    return f"{round(filterRMSE, 2)}RMSE-{CMA_WINDOW_SIZE if WITH_CMA else 'no'}CMA-{P}P-{R}R-{Q}Q-{SMOOTHING_FACTOR if WITH_SMOOTHING else 'no'}Smooth-{len(allData)}Samples-{ANCHOR_COUNT}Anch-{str(NOISE_STD_DEV)+'ns' if WITH_NOISE else 'no'}Noise"

def generateTestDescParams():
    return f"{CMA_WINDOW_SIZE if WITH_CMA else 'no'}CMA-{P}P-{R}R-{Q}Q-{SMOOTHING_FACTOR if WITH_SMOOTHING else 'no'}Smooth-{ANCHOR_COUNT}Anch-{str(NOISE_STD_DEV)+'ns' if WITH_NOISE else 'no'}Noise"


def estimateVelocityMedian(numPoints):
    if len(filterEstLocs) < numPoints:
        return [0, 0]
    loc = filterEstLocs[-1]
    velocties = dict()
    dt = 0.12
    for i in range(numPoints-1):
        compLoc = filterEstLocs[-2-i]
        vX = (loc[0] - compLoc[0])/(dt * (i+1))
        vY = (loc[1] - compLoc[1])/(dt * (i+1))
        v = math.sqrt(vX**2 + vY**2)
        velocties[v] = [vX, vY]
    median = sorted(velocties.keys())[numPoints//2]
    return velocties[median]

def estimateVelocityWindow(windowSize):
    if len(filterEstLocs) < windowSize+1:
        return [0, 0]
    dt = 0.12
    loc = filterEstLocs[-1]
    compLoc = filterEstLocs[-1-windowSize]
    vX = (loc[0] - compLoc[0])/(dt * (windowSize))
    vY = (loc[1] - compLoc[1])/(dt * (windowSize))
    return [vX, vY]

def smooth(val, lastVal):
    if WITH_SMOOTHING==False: return val
    newVal = []
    for i in range(2):
        newVal.append(lastVal[i] + ((val[i] - lastVal[i]) / SMOOTHING_FACTOR))
    return newVal

def localizeSinglePoint(dataPoint):
    simulatedData = pulseAndStamp(dataPoint)

    T = [None]*len(ANCHORS)
    for info in simulatedData:
        T[info["anchID"]] = info["TOA"]
    tau = [None]*len(ANCHORS) #all based on reference anchor 0
    for id, t in enumerate(T):
        tau[id] = t - T[0]
        if tau[id]==0: tau[id] = 1*10**-9
    # app.taus.append(tau)
    # print(tau)
    times.append(round(simulatedData[0]["syncTime"]/1e9, 4))

    x, y = dataPoint[REAL_X], dataPoint[REAL_Y]
    realLocs.append((x, y))
    
    linX, linY = linearLocalization(T, tau) if LINEAR_ON else (0,0)
    linEstLocs.append((linX, linY))
    
    nLinX, nLinY = nonLinearLocalization(T, tau) if HYPERBOLA_ON else (0,0)
    nonLinEstLocs.append((nLinX, nLinY))
    
    velocity = estimateVelocityWindow(1)
    #smoothVel = smooth(velocity, realVels[-1])
    realVels.append(velocity)

    if len(filterEstLocs) == 0:
        filtX, filtY = EKF.estimate(T, velocity)
        filterEstLocs.append((filtX, filtY))
    else:
        lastLoc = filterEstLocs[-1]
        smoothX, smoothY = smooth(EKF.estimate(T, velocity), filterEstLocs[-1])
        filterEstLocs.append((smoothX, smoothY))

    # print("\nREPORT:")
    # print(f"Actual:", app.realLocs[-1][0], app.realLocs[-1][1])
    # print(f"Linear:", app.linEstLocs[-1][0], app.linEstLocs[-1][1])
    # print(f"Non-Linear:", app.nonLinEstLocs[-1][0], app.nonLinEstLocs[-1][1])
    # print(f"Extended Kalman Filter:", app.filterEstLocs[-1][0], app.filterEstLocs[-1][1])
    # print("End Report:\n")

def pulseAndStamp(dataPoint):
    timeStampTuples = []
    anchorSyncTimeNS = dataPoint[TIME]*1e6 #convert from ms to ns
    x = dataPoint[REAL_X]
    y = dataPoint[REAL_Y]
    for anch_id, anchor in enumerate(ANCHORS):
        anchorX, anchorY = anchor #feet
        d = euclidDist(x, y, anchorX, anchorY)
        t = metersToNanosec(d)
        noise = 0
        if WITH_NOISE:
            noise = np.random.normal(0, NOISE_STD_DEV)
        tof=round(t+noise)
        info = dict()
        info['anchID'] = anch_id
        info['syncTime'] = anchorSyncTimeNS
        info['pureTOF'] = round(t)
        info['noise'] = noise
        info['noisyTOF'] = tof
        info['TOA'] = anchorSyncTimeNS+tof
        timeStampTuples.append(info)
    timeStampTuples.sort(key= lambda x: x["noisyTOF"])
    return timeStampTuples

def linearLocalization(T, tau):
    v = SPEED_OF_LIGHT / (1e9) # meters per nanosecond
    x = list(map(lambda x: x[0], ANCHORS))
    y = list(map(lambda x: x[1], ANCHORS))
    alpha = [None]*len(ANCHORS)
    beta = [None]*len(ANCHORS)
    gamma = [None]*len(ANCHORS)
    for m in range(2, len(ANCHORS)):
        alpha[m] = ((1/(v*tau[m]))*(-2*x[0]+2*x[m]))-((1/(v*tau[1]))*(2*x[1]-2*x[0]))
        beta[m] = ((1/(v*tau[m]))*(-2*y[0]+2*y[m]))-((1/(v*tau[1]))*(2*y[1]-2*y[0]))
        sum1 = (x[0]**2)+(y[0]**2)-(x[m]**2)-(y[m]**2)
        sum2 = (x[0]**2)+(y[0]**2)-(x[1]**2)-(y[1]**2)
        gamma[m] = v*tau[m]-v*tau[1]+(1/(v*tau[m]))*sum1-(1/(v*tau[1]))*sum2
    A = make2dList(len(ANCHORS)-2, 2)
    B = [None]*(len(ANCHORS)-2)
    for m in range(2, len(ANCHORS)):
        A[m-2][0] = alpha[m]
        A[m-2][1] = beta[m]
        B[m-2] = gamma[m]
    # print(alpha)
    # print(beta)
    # print(gamma)
    # print(A)
    # print(B)
    estX, estY = np.linalg.lstsq(np.array(A), np.array(B), rcond=None)[0]
    return((-estX, -estY))
    # x2, y2 = spo.lsq_linear(np.array(A), np.array(B)).x
    # ans2 = np.linalg.solve(np.array(A), np.array(B))
    # print(ans2)
    # print("\n")
    # print((app.linEstX, app.linEstY))
    # print((-x2, -y2))
    
def nonLinearLocalization(T, tau):
    v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
    x = list(map(lambda x: x[0], ANCHORS))
    y = list(map(lambda x: x[1], ANCHORS))
    def hyperbolas(var):
        X = var[0]
        Y = var[1]
        hs = np.zeros(len(ANCHORS)-1)
        for m in range(1, len(ANCHORS)):
            c = x[m]**2-x[0]**2+y[m]**2-y[0]**2-(v*tau[m])**2
            xTerm = (2*x[m]-2*x[0])*X
            yTerm = (2*y[m]-2*y[0])*Y
            root = (2*v*tau[m])*math.sqrt((x[0]-X)**2+(y[0]-Y)**2)
            hs[m-1] = c-xTerm-yTerm-root
        return hs
    lastEstX, lastEstY = nonLinEstLocs[-1] if len(nonLinEstLocs)>0 else linEstLocs[-1]
    guess = np.array([lastEstX, lastEstY])
    estX, estY = spo.least_squares(hyperbolas, guess).x
    return (estX, estY)

class ExtKalmanFilter(object):
    def __init__(self):
        if (VELOCITY):
            self.f = ExtendedKalmanFilter(dim_x=4, dim_z=(len(ANCHORS)-1+2))
            # The estimate
            self.f.x = np.array([[1.],
                                [1.],
                                [0.],
                                [0.]])
            # State transition matrix, just use last position for now
            self.f.F = np.array([[1., 0., 0.12, 0.],
                                [0., 1., 0.,   0.12],
                                [0., 0., 1.,   0.],
                                [0., 0., 0.,   1.]])
            # Measurement function, values from linear localization
            self.f.P = np.eye(4) * P                 # Covaraince, large number since our initial guess is (1, 1)
            self.f.R = np.eye(len(ANCHORS)-1+2) * R  # Measurement uncertainty, making it high since noisy data
            self.f.Q = np.eye(4) * Q                 # System noise, making it small since we're using a velocity estimation
        
        else:
            self.f = ExtendedKalmanFilter(dim_x=2, dim_z=len(ANCHORS)-1)
            # The estimate
            self.f.x = np.array([[1.],
                                [1.]])
            # State transition matrix, just use last position for now
            self.f.F = np.array([[1., 0.],
                                [0., 1.]])
            # Measurement function, values from linear localization
            self.f.P = np.eye(2) * P                # Covaraince, large number since our initial guess is (1, 1)
            self.f.R = np.eye(len(ANCHORS)-1) * R   # Measurement uncertainty, making it low since we want to weight sensor data
            self.f.Q = np.eye(2) * Q                # System noise, making it big since we're just using the last location as our prediction
        
    def h(self, state):
        times = []
        x, y = state[0][0], state[1][0]
        v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
        anchor_0 = ANCHORS[0]
        D_0 = math.sqrt(((anchor_0[0] - x) ** 2) + ((anchor_0[1] - y) ** 2))
        for anchor in ANCHORS[1:]:
            D_n = math.sqrt(((anchor[0] - x) ** 2) + ((anchor[1] - y) ** 2))
            tau_0n = D_0 - D_n
            times.append([tau_0n / v])
        if VELOCITY:
            times.append([state[2][0]])
            times.append([state[3][0]])
        return np.array(times)

    def jacobian(self, state):
        if VELOCITY:
            x, y, vx, vy = sympy.symbols('x, y, vx, vy')
        else:
            x, y = sympy.symbols('x, y')

        h = []
        v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
        anchor_0 = ANCHORS[0]
        D_0 = sympy.sqrt(((anchor_0[0] - x) ** 2) + ((anchor_0[1] - y) ** 2))
        for anchor in ANCHORS[1:]:
            D_n = sympy.sqrt(((anchor[0] - x) ** 2) + ((anchor[1] - y) ** 2))
            tau_0n = D_0 - D_n
            h.append([tau_0n / v])
        if VELOCITY:
            h.append([vx])
            h.append([vy])
        H = sympy.Matrix(h)
        
        if VELOCITY:
            H = H.jacobian(sympy.Matrix([x, y, vx, vy]))
            return np.array(H.subs([(x, state[0][0]), (y, state[1][0]), (vx, state[2][0]), (vy, state[3][0])])).astype(float)
        else:
            H = H.jacobian(sympy.Matrix([x, y]))
            return np.array(H.subs([(x, state[0][0]), (y, state[1][0])])).astype(float)

    def estimate(self, T, velocity):
        z = []
        for n in range(1, len(ANCHORS)):
            z.append([T[0] - T[n]])
        if VELOCITY:
            z.append([velocity[0]])
            z.append([velocity[1]])
        z = np.array(z)
        # print("last location:", self.lastLoc[0], ",", self.lastLoc[1])
        # print("current location:", self.f.x[0][0], ",", self.f.x[1][0])
        # print("velocity:", z[-2][0], ",", z[-1][0])
        
        self.f.predict()
        self.f.update(z, self.jacobian, self.h)

        estX = self.f.x[0][0]
        estY = self.f.x[1][0]
        if VELOCITY:
            filterVels.append((self.f.x[2][0], self.f.x[3][0]))
        return (estX, estY)

gameFile = "0021500003-NOPatGSW-2015-10-27"
dataPath = f"test_data{os.sep}{gameFile}"
testSet = []
try:
    start, end = tuple(map(int, sys.argv[1:]))
    print("Running tests for set:" + str(os.listdir(dataPath)[start:end]))
    testSet.extend(os.listdir(dataPath)[start:end])
    # pIndex, rVal = tuple(map(int, sys.argv[1:]))
except:
    player = input("Pick a player name").lower()
    playerFold = list(filter(lambda p:player in p.lower(), os.listdir(dataPath)))[0]
    print("Running tests for set:" + str(playerFold))
    testSet.append(playerFold)

# parmValsEKF = [1, 10, 100, 1000, 10000, 100000]

for playerFolder in testSet:
    dirPath = f"{dataPath}{os.sep}{playerFolder}"
    for playerPath in os.listdir(dirPath):
        playerPath = playerPath.strip('.csv')
        path = dirPath + os.sep + playerPath
        print(f"Simulating for dataset: {playerPath}")

        allData = []
        with open(path+'.csv', 'r') as f:
            cR = csv.DictReader(f)
            # next(cR) # skip header
            sampleCount = 0
            for row in cR:
                if MAX_SAMPLE_COUNT!=None and sampleCount >= MAX_SAMPLE_COUNT: break
                row[SAMPLE_IDX] = int(row[SAMPLE_IDX])
                row[TIME] = int(row[TIME])
                row[GAME_TIME] = float(row[GAME_TIME])
                row[PLAYER_ID] = int(row[PLAYER_ID])
                row[REAL_X], row[REAL_Y] = float(row[REAL_X]), float(row[REAL_Y])
                allData.append(row)
                sampleCount+=1

        times = []
        realLocs = []
        linEstLocs = []
        nonLinEstLocs = []
        filterEstLocs = []
        realVels = [(0, 0)]
        filterVels = [(0, 0)]
        EKF = ExtKalmanFilter()

        # logging = input("Log simulation results?(y/n)")=='y'
        logging = True
        # graphing = input("Graph simulation results?(y/n)")=='y'
        graphing = False

        # print("Starting to simulate samples")
        counter = 0
        t = time.time()
        for sample in allData:
            localizeSinglePoint(sample)
            counter+=1
            if counter%100==0:
                # print(f"Simulated {counter} samples in {round(time.time()-t, 1)} seconds")
                t = time.time()

        print(f"Done simulating samples.")

        # central moving average on filtered estimates
        if WITH_CMA:
            for i in range(CMA_WINDOW_SIZE//2, len(filterEstLocs)):
                xs, ys = zip(*filterEstLocs[i-CMA_WINDOW_SIZE//2:i-CMA_WINDOW_SIZE//2+CMA_WINDOW_SIZE])
                filterEstLocs[i] = round(np.mean(xs), 4), round(np.mean(ys), 4)

        # remove samples that were part of calibration
        # for data in [allData, times, realLocs, linEstLocs, nonLinEstLocs, filterEstLocs]:
        #     data = data[CALIBRATION_SAMPLES:]
        allData = allData[CALIBRATION_SAMPLES:]
        times = times[CALIBRATION_SAMPLES:]
        realLocs = realLocs[CALIBRATION_SAMPLES:]
        linEstLocs = linEstLocs[CALIBRATION_SAMPLES:]
        nonLinEstLocs = nonLinEstLocs[CALIBRATION_SAMPLES:]
        filterEstLocs = filterEstLocs[CALIBRATION_SAMPLES:]

        linErrs = []
        nonLinErrs = []
        filterErrs = []
        for i, (x, y) in enumerate(realLocs):
            estX, estY = linEstLocs[i]
            linErrs.append(euclidDist(x, y, estX, estY))
            estX, estY = nonLinEstLocs[i]
            nonLinErrs.append(euclidDist(x, y, estX, estY))
            estX, estY = filterEstLocs[i]
            filterErrs.append(euclidDist(x, y, estX, estY))

        vels = [(0,0)]
        for i in range(1, len(realLocs)):
            oldT, T = times[i-1], times[i]
            oldX, oldY = realLocs[i-1]
            X, Y = realLocs[i]
            velX = (X-oldX)/(T-oldT)
            velY = (Y-oldY)/(T-oldT)
            vels.append((velX, velY))

        linNP = np.array(linErrs)
        hypNP = np.array(nonLinErrs)
        filtNP = np.array(filterErrs)
        linRMSE = rmse(linNP)
        nonLinRMSE = rmse(hypNP)
        filterRMSE = rmse(filtNP)

        if logging:
            fDesc = generateTestDesc()
            # print("Logging samples")
            # write sim to file
            locDir = "nba_train_logs"
            outDir = f"{locDir}{os.sep}{gameFile}{os.sep}{playerFolder}{os.sep}{playerPath}"
            if not os.path.exists(outDir): os.makedirs(outDir)
            with open(f"{outDir}{os.sep}{fDesc}.csv", "w", newline='') as f:
                cW = csv.writer(f)
                cW.writerow(out_headers)
                for i in range(len(allData)):
                    # time.sleep(0.001)
                    cW.writerow(list(map(lambda x: round(x, 4), [i,
                                                            times[i]-times[0],
                                                            allData[i][GAME_TIME],
                                                            allData[i][PLAYER_ID],
                                                            realLocs[i][0],
                                                            realLocs[i][1],
                                                            vels[i][0],
                                                            vels[i][1],
                                                            linEstLocs[i][0],
                                                            linEstLocs[i][1],
                                                            nonLinEstLocs[i][0],
                                                            nonLinEstLocs[i][1],
                                                            filterEstLocs[i][0],
                                                            filterEstLocs[i][1],
                                                            linErrs[i],
                                                            nonLinErrs[i],
                                                            filterErrs[i],
                                                            linRMSE,
                                                            nonLinRMSE,
                                                            filterRMSE])))
            fComb = generateTestDescParams()
            f = open(f"{locDir}{os.sep}0_{fComb}.txt", "a")  # append mode 
            f.write(f"{round(filterRMSE, 4)}\n")
            f.close()

# print("*"*40, "\n"+"Error Report (RMSE in Meters):")
# print("Linear Lst Sq:", round(linRMSE,4))
# print("Hyperbolic Lst Sq:", round(nonLinRMSE, 4))
# print("Ext. Kalman Filt:", round(filterRMSE, 4))
# print("END Report", "\n"+"*"*40)

# if graphing:
#     x = np.arange(0, len(linNP))
#     if LINEAR_ON: plt.plot(x, linNP, color=linColor, marker='o', label="Linear Error")
#     if HYPERBOLA_ON: plt.plot(x, hypNP, color=hypColor, marker='o', label="Non-linear Error")
#     plt.plot(x, filtNP, color=filterColor, marker='o', label="Kalman Filter Error")
#     plt.legend()
#     plt.show()