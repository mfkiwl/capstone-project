from cmu_112_graphics import * 
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
import tkinter
from basketball_mapping import *
pp = pprint.PrettyPrinter()
pprint = pp.pprint
ANCHORS = None 

##TEST SIMULATION PARAMETERS#########
WITH_NOISE = True
NOISE_STD_DEV = 1.5 #nanoseconds
PULSE_FREQ = 2
tagColor = 'black'
anchorColor = 'red'
linColor = 'purple'
nonLinColor = 'green'
filterColor = 'blue'
##################################
ANCHOR_COUNT = 6
ANCHORS = [(0,0), (0, footToMeter(COURT_HEIGHT_FEET)),
            (footToMeter(COURT_WIDTH_FEET), 0), (footToMeter(COURT_WIDTH_FEET), footToMeter(COURT_HEIGHT_FEET)),
            (footToMeter(COURT_WIDTH_FEET//2), 0), (footToMeter(COURT_WIDTH_FEET//2), footToMeter(COURT_HEIGHT_FEET))][:ANCHOR_COUNT]
out_rows = ["Sample_idx", "sample_time", "realX", "realY", "linEstX", "linEstY", "hypEstX", "hypEstY","filtEstX", "filtEstY", "linErr", "hypErr", "filtErr", "linRMSE", "hypRMSE", "filtRMSE"]

def generateTestDesc(app):
    desc = app.getUserInput("Path Description?")
    if WITH_NOISE:
        desc = f"{len(ANCHORS)}Anch-{NOISE_STD_DEV}nsNoise-{PULSE_FREQ}Freq-{desc}"
    else:
        desc = f"{len(ANCHORS)}Anch-noNoise-{PULSE_FREQ}Freq-{desc}"
    return desc

class Tag(object):
    def __init__(self, x, y, id, color=tagColor):
        self.x = x
        self.y = y
        self.id = id
        self.color = color

def pulseAndStamp(app):
    timeStampTuples = []
    anchorSyncTime = time.time_ns()
    # print(f"syncTime:{anchorSyncTime}")
    for anchID, anchor in enumerate(app.anchors):
        d = euclidDist(app.tag.x, app.tag.y, anchor[0], anchor[1])
        # d = distanceBetween(app.tag, anchor)
        t = metersToNanosec(d)
        noise = 0
        if WITH_NOISE:
            noise = np.random.normal(0, NOISE_STD_DEV)
        tof=round(t+noise)
        info = dict()
        info['tagID'] = app.tag.id
        info['anchID'] = anchID
        info['syncTime'] = anchorSyncTime
        info['actTOF'] = round(t)
        info['noise'] = noise
        info['simTOF'] = tof
        info['timestamp'] = anchorSyncTime+tof
        timeStampTuples.append(info)
    timeStampTuples.sort(key= lambda x: x["simTOF"])
    return timeStampTuples

def linearLocalization(app, T, tau):
    v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
    x = app.xs
    y = app.ys        
    alpha = [None]*len(app.anchors)
    beta = [None]*len(app.anchors)
    gamma = [None]*len(app.anchors)
    for m in range(2, len(app.anchors)):
        alpha[m] = ((1/(v*tau[m]))*(-2*x[0]+2*x[m]))-((1/(v*tau[1]))*(2*x[1]-2*x[0]))
        beta[m] = ((1/(v*tau[m]))*(-2*y[0]+2*y[m]))-((1/(v*tau[1]))*(2*y[1]-2*y[0]))
        sum1 = (x[0]**2)+(y[0]**2)-(x[m]**2)-(y[m]**2)
        sum2 = (x[0]**2)+(y[0]**2)-(x[1]**2)-(y[1]**2)
        gamma[m] = v*tau[m]-v*tau[1]+(1/(v*tau[m]))*sum1-(1/(v*tau[1]))*sum2
    A = make2dList(len(app.anchors)-2, 2)
    B = [None]*(len(app.anchors)-2)
    for m in range(2, len(app.anchors)):
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
    
def nonLinearLocalization(app, T, tau):
    v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
    x = app.xs
    y = app.ys
    def hyperbolas(var):
        X = var[0]
        Y = var[1]
        hs = np.zeros(len(app.anchors)-1)
        for m in range(1, len(app.anchors)):
            c = x[m]**2-x[0]**2+y[m]**2-y[0]**2-(v*tau[m])**2
            xTerm = (2*x[m]-2*x[0])*X
            yTerm = (2*y[m]-2*y[0])*Y
            root = (2*v*tau[m])*math.sqrt((x[0]-X)**2+(y[0]-Y)**2)
            hs[m-1] = c-xTerm-yTerm-root
        return hs
    lastEstX, lastEstY = app.nonLinEstLocs[-1] if len(app.nonLinEstLocs)>0 else gridToCoord(app.rows//2, app.cols//2)
    guess = np.array([lastEstX, lastEstY])
    estX, estY = spo.least_squares(hyperbolas, guess).x
    return (estX, estY)

def h(state):
    times = []
    x, y = state[0][0], state[1][0]
    v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
    anchor_0 = ANCHORS[0]
    D_0 = math.sqrt(((anchor_0[0] - x) ** 2) + ((anchor_0[1] - y) ** 2))
    for anchor in ANCHORS[1:]:
        D_n = math.sqrt(((anchor[0] - x) ** 2) + ((anchor[1] - y) ** 2))
        tau_0n = D_0 - D_n
        times.append([tau_0n / v])
    return np.array(times)

def jacobian(state):
    x, y = sympy.symbols('x, y')
    h = []
    v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
    anchor_0 = ANCHORS[0]
    D_0 = sympy.sqrt(((anchor_0[0] - x) ** 2) + ((anchor_0[1] - y) ** 2))
    for anchor in ANCHORS[1:]:
        D_n = sympy.sqrt(((anchor[0] - x) ** 2) + ((anchor[1] - y) ** 2))
        tau_0n = D_0 - D_n
        h.append([tau_0n / v])
    H = sympy.Matrix(h)
    H = H.jacobian(sympy.Matrix([x, y]))
    return np.array(H.subs([(x, state[0][0]), (y, state[1][0])])).astype(float)
    
def initFilter(app):
    app.f = ExtendedKalmanFilter(dim_x=2, dim_z=len(ANCHORS)-1)
    # The estimate
    app.f.x = np.array([[1.],
                        [1.]])
    # State transition matrix, just use last position for now
    app.f.F = np.array([[1., 0.],
                        [0., 1.]])
    # Measurement function, values from linear localization
    app.f.P = np.eye(2) * 1000              # Covaraince, large number since our initial guess is (1, 1)
    app.f.R = np.eye(len(ANCHORS)-1) * 50   # Measurement uncertainty, making it low since we want to weight sensor data
    app.f.Q = np.eye(2) * 1                 # System noise, making it big since we're just using the last location as our prediction
    
def extendedKalmanEst(app, timestamps):
    # z = np.array(timestamps)
    T = [None]*len(app.anchors)
    for (id, stamp) in timestamps:
        T[id] = stamp
    z = []
    for n in range(1, len(app.anchors)):
        z.append([T[0] - T[n]])
    z = np.array(z)
    app.f.predict()
    app.f.update(z, jacobian, h)

    estX = app.f.x[0][0]
    estY = app.f.x[1][0]
    return (estX, estY)

def runLocalization(app):
    simulatedData = pulseAndStamp(app)
    app.simulatedData = simulatedData
    # justTimeStamps = list(map(lambda x: (x["anchID"], x["timestamp"]), simulatedData))

    # T = [None]*len(app.anchors)
    # for info in simulatedData:
    #     T[info["anchID"]] = info["timestamp"]
    # tau = [None]*len(app.anchors) #all based on reference anchor 0
    # for id, t in enumerate(T):
    #     tau[id] = t - T[0]
    #     if tau[id]==0: tau[id] = 1*10**-9
    # app.taus.append(tau)
    # # print(tau)
    # # x, y = gridToCoord(app.tag.row, app.tag.col)
    # x, y = app.tag.x, app.tag.y
    # linX, linY = linearLocalization(app, T, tau)
    # nLinX, nLinY = nonLinearLocalization(app, T, tau)
    # filtX, filtY = extendedKalmanEst(app, justTimeStamps)
    # if app.isCollecting:
    #     app.times.append(round(simulatedData[0]["syncTime"]/1e9, 4))
    #     app.realLocs.append((x, y))
    #     app.linEstLocs.append((linX, linY))
    #     app.nonLinEstLocs.append((nLinX, nLinY))
    #     app.filterEstLocs.append((filtX, filtY))
    #     # print("\nREPORT:")
    #     # print(f"Actual:", app.realLocs[-1][0], app.realLocs[-1][1])
    #     # print(f"Linear:", app.linEstLocs[-1][0], app.linEstLocs[-1][1])
    #     # print(f"Non-Linear:", app.nonLinEstLocs[-1][0], app.nonLinEstLocs[-1][1])
    #     # print(f"Extended Kalman Filter:", app.filterEstLocs[-1][0], app.filterEstLocs[-1][1])
    #     # print("End Report:\n")

def appStarted(app):
    app.pulseInterval = 1000//PULSE_FREQ
    app.counter=0
    app.time = 0
    app.timerDelay = 50
    app.isCollecting = False
    app.simulatedData = []
    app.margin = APP_MARGIN
    app.cols = COURT_WIDTH_FEET//FEET_IN_GRID # 100 feet court width
    app.rows = COURT_HEIGHT_FEET//FEET_IN_GRID  # 50 feet court height
    app.tag = Tag(footToMeter(COURT_WIDTH_FEET/2), footToMeter(COURT_HEIGHT_FEET/2), "Player 1")
    app.anchors = ANCHORS
    app.xs = [None]*len(app.anchors)
    app.ys = [None]*len(app.anchors)
    for anchid, anchor in enumerate(app.anchors):
        app.xs[anchid], app.ys[anchid] = anchor[0], anchor[1]

    app.realLocs = []
    app.linEstLocs = []
    app.nonLinEstLocs = []
    app.filterEstLocs = []
    app.taus = []
    app.times = []
    # app.court = app.loadImage('https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Basketball_court_fiba.svg/440px-Basketball_court_fiba.svg.png').transpose(Image.ROTATE_90).resize((1000,500))
    # app.court = app.loadImage('https://raw.githubusercontent.com/savvastj/nbaPlayerTracking/master/fullcourt.png').resize((app.width-2*app.margin,app.height-2*app.margin))
    # app.court = app.loadImage('https://i.imgur.com/YBcbBFq.png').transpose(Image.ROTATE_90).resize((app.width-2*app.margin,app.height-2*app.margin))
    app.court = app.loadImage('decolored-court.png').transpose(Image.ROTATE_90).resize((app.width-2*app.margin,app.height-2*app.margin))
    app.court.putalpha(50)
    initFilter(app)
    
def keyPressed(app, event):
    if (event.key == 'Up'):      app.tag.y -= 0.2
    elif (event.key == 'Down'):  app.tag.y += 0.2
    elif (event.key == 'Left'):  app.tag.x -= 0.2
    elif (event.key == 'Right'): app.tag.x += 0.2
    elif (event.key == 'Space'): app.isCollecting = not app.isCollecting

def mouseDragged(app, event):
    app.tag.x, app.tag.y = pixelToMeter(app, event.x, event.y)

def timerFired(app):
    app.time += app.timerDelay
    if app.time%app.pulseInterval==0:
        app.counter+=1
        # t=time.time()
        runLocalization(app)
        # print(f"Ran {app.counter} localization at {app.time/1000}! Took {time.time()-t} seconds")

def appStopped(app):
    store = app.getUserInput("Do you want to log sim information?(y/n)")=='y'
    graph = app.getUserInput("Do you want to show error graph? (y/n)")=='y'
    
    # create error reports after app is closed
    print("*"*40, "\n"+"Error Report (RMSE in Meters):")
    linErrs = []
    nonLinErrs = []
    filterErrs = []
    for i, (x, y) in enumerate(app.realLocs):
        estX, estY = app.linEstLocs[i]
        linErrs.append(euclidDist(x, y, estX, estY))
        estX, estY = app.nonLinEstLocs[i]
        nonLinErrs.append(euclidDist(x, y, estX, estY))
        estX, estY = app.filterEstLocs[i]
        filterErrs.append(euclidDist(x, y, estX, estY))
    
    x = np.arange(0, len(linErrs))
    linNP = np.array(linErrs)
    hypNP = np.array(nonLinErrs)
    filtNP = np.array(filterErrs)
    linRMSE = rmse(linNP)
    nonLinRMSE = rmse(hypNP)
    filterRMSE = rmse(filtNP)

    if store:
        # write sim to file
        name = generateTestDesc(app)
        with open(f"sim_logs/{name}.csv", "w", newline='') as f:
            cW = csv.writer(f)
            cW.writerow(out_rows)
            for i in range(len(app.realLocs)):
                time.sleep(0.01)
                cW.writerow(list(map(lambda x: round(x, 4), [i,
                                                            app.times[i]-app.times[0],
                                                            app.realLocs[i][0],
                                                            app.realLocs[i][1],
                                                            app.linEstLocs[i][0],
                                                            app.linEstLocs[i][1],
                                                            app.nonLinEstLocs[i][0],
                                                            app.nonLinEstLocs[i][1],
                                                            app.filterEstLocs[i][0],
                                                            app.filterEstLocs[i][1],
                                                            linErrs[i],
                                                            nonLinErrs[i],
                                                            filterErrs[i],
                                                            linRMSE,
                                                            nonLinRMSE,
                                                            filterRMSE])))
    

    print("Linear Lst Sq:", round(meterToFoot(linRMSE),4))
    print("Hyperbolic Lst Sq:", round(meterToFoot(nonLinRMSE), 4))
    print("Ext. Kalman Filt:", round(meterToFoot(filterRMSE), 4))
    # print("nonLin / filter RMSE:", round(nonLinRMSE/filterRMSE,4))
    print("END Report", "\n"+"*"*40)

    if graph:
        plt.plot(x, linErrs, color=linColor, marker='o', label="Linear Error")
        plt.plot(x, nonLinErrs, color=nonLinColor, marker='o', label="Non-linear Error")
        plt.plot(x, filterErrs, color=filterColor, marker='o', label="Kalman Filter Error")
        plt.legend()
        plt.show()

def drawX(canvas, cX, cY, w, color):
    x0, y0, x1, y1, x2, y2, x3, y3 = cX-w, cY-w, cX+w, cY-w, cX-w, cY+w, cX+w, cY+w
    canvas.create_line(x0, y0, x3, y3, fill=color, width=3)
    canvas.create_line(x2, y2, x1, y1, fill=color, width=3)

def redrawAll(app, canvas):
    canvas.create_image(app.width//2, app.height//2, image=ImageTk.PhotoImage(app.court))
    canvas.create_text(app.width//2, app.margin//2, text=f"NOISE:{NOISE_STD_DEV}, ANCHORS: {ANCHOR_COUNT},  PULSE_FREQUENCY:{PULSE_FREQ}")
    canvas.create_text(app.width//2, app.height-15, text=f"Pulses:{app.counter}")

    # draw tags
    r = 10
    cX, cY = meterToPixel(app, app.tag.x, app.tag.y)
    canvas.create_oval(cX-r, cY-r, cX+r, cY+r, fill=None, outline=app.tag.color, width = 3)

    for id, anchor in enumerate(app.anchors):
        r = 10
        cx, cy = metersToPixel(app, anchor[0], anchor[1])
        canvas.create_rectangle(cx-r, cy-r, cx+r, cy+r, fill="red")
        canvas.create_text(cx, cy, text=f'{id}')
        if app.time%app.pulseInterval==0:
            for d in app.simulatedData:
                if d["anchID"]==id:
                    canvas.create_text(cx, cy+2*r, text=f'ToF:{d["simTOF"]}ns', fill="purple")
            canvas.create_line(cX, cY, cx, cy, fill="purple", width=3, arrow="last")
        else:
            for d in app.simulatedData:
                if d["anchID"]==id:
                    canvas.create_text(cx, cy+2*r, text=f'ToF:{d["simTOF"]}ns', fill="black")


    r = 3
    if len(app.linEstLocs)>0:
        estX, estY = app.linEstLocs[-1]
        estX, estY = metersToPixel(app, estX, estY)
        drawX(canvas, estX, estY, r, linColor)
        # r, c = coordToGrid(estX, estY)
        # (x0, y0, x1, y1) = getCellBounds(app, r, c)
        # canvas.create_rectangle(x0, y0, x1, y1, fill=linColor)

    if len(app.nonLinEstLocs)>0:
        estX, estY = app.nonLinEstLocs[-1]
        estX, estY = metersToPixel(app, estX, estY)
        drawX(canvas, estX, estY, r, nonLinColor)
        # r, c = coordToGrid(estX, estY)
        # (x0, y0, x1, y1) = getCellBounds(app, r, c)
        # canvas.create_rectangle(x0, y0, x1, y1, fill=nonLinColor)

    if len(app.filterEstLocs)>0:
        estX, estY = app.filterEstLocs[-1]
        estX, estY = metersToPixel(app, estX, estY)
        drawX(canvas, estX, estY, r, filterColor)
        # r, c = coordToGrid(estX, estY)
        # (x0, y0, x1, y1) = getCellBounds(app, r, c)
        # canvas.create_rectangle(x0, y0, x1, y1, fill=filterColor)



runApp(width=APP_WIDTH, height=APP_HEIGHT)