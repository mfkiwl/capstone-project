import module_manager
module_manager.review()

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
pp = pprint.PrettyPrinter()
ANCHORS = None 

##TEST SIMULATION PARAMETERS#########
WITH_NOISE = True
NOISE_STD_DEV = 2.5 #nanoseconds
PULSE_FREQ = 10
tagColor = 'black'
anchorColor = 'red'
linColor = 'purple'
nonLinColor = 'green'
filterColor = 'blue'
##################################
#CONSTANTS#
METERS_IN_FOOT = 0.304800000
FEET_IN_GRID = 1
SPEED_OF_LIGHT = 299702547 # m/s in air
#######################################


def make2dList(rows, cols):
    return [ ([None] * cols) for row in range(rows) ]

def getCellBounds(app, row, col):
    gridWidth  = app.width - 2*app.margin
    gridHeight = app.height - 2*app.margin
    x0 = app.margin + gridWidth * col / app.cols
    x1 = app.margin + gridWidth * (col+1) / app.cols
    y0 = app.margin + gridHeight * row / app.rows
    y1 = app.margin + gridHeight * (row+1) / app.rows
    return (x0, y0, x1, y1)

def metersToPixel(app, x, y):
    pixelWidth  = app.width - 2*app.margin
    pixelHeight = app.height - 2*app.margin
    pixelsInFootW = pixelWidth/100
    pixelsInFootH = pixelHeight/50
    pixX = x/METERS_IN_FOOT*pixelsInFootW+app.margin
    pixY = y/METERS_IN_FOOT*pixelsInFootH+app.margin
    return (pixX, pixY)
    

def gridToCoord(row, col):
    return ((col * FEET_IN_GRID + FEET_IN_GRID/2) * METERS_IN_FOOT, (row * FEET_IN_GRID + FEET_IN_GRID/2) * METERS_IN_FOOT)

def coordToGrid(x, y): #coord to row/col number
    feetX = x/METERS_IN_FOOT
    feetY = y/METERS_IN_FOOT
    return (int(feetY//FEET_IN_GRID), int(feetX//FEET_IN_GRID))

def generateTestDesc(app):
    pathDesc = app.getUserInput("Path Description?")
    desc = f"{len(ANCHORS)}A-Err:{WITH_NOISE}-Path:{pathDesc}"
    return desc

class Tag(object):
    def __init__(self, row, col, id, color=tagColor):
        self.row = row
        self.col = col
        self.id = id
        self.color = color

class Anchor(object):
    def __init__(self, row, col, id, color=anchorColor):
        self.row = row
        self.col = col
        self.color = color
        self.id = id

def euclidDist(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

def distanceBetween(tag, anchor):
    dRow = abs(tag.row - anchor.row)
    dCol = abs(tag.col - anchor.col)
    dXMeters = dRow*METERS_IN_FOOT
    dYMeters = dCol*METERS_IN_FOOT
    d = math.sqrt(dXMeters**2+dYMeters**2)
    return d

def metersToNanosec(d):
    return (d/SPEED_OF_LIGHT)*10**9

def pulseAndStamp(app):
    timeStampTuples = []
    anchorSyncTime = time.time_ns()
    # print(f"syncTime:{anchorSyncTime}")
    for anchor in app.anchors:
        d = distanceBetween(app.tag, anchor)
        t = metersToNanosec(d)
        noise = 0
        if WITH_NOISE:
            noise = np.random.normal(0, NOISE_STD_DEV)
        tof=round(t+noise)
        timeStampTuples.append((app.tag.id, anchor.id, round(t), anchorSyncTime+tof))
    timeStampTuples.sort(key= lambda x: x[2])
    return timeStampTuples

def linearLocalization(app, timestamps):
    v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
    x = app.xs
    y = app.ys
    T = [None]*len(app.anchors)
    for (id, stamp) in timestamps:
        T[id] = stamp
    tau = [None]*len(app.anchors) #all based on reference anchor 0
    for id, t in enumerate(T):
        tau[id] = t - T[0]
        if tau[id]==0: tau[id] = 1*10**-9
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
    
def nonLinearLocalization(app, timestamps):
    v = SPEED_OF_LIGHT / (10**9) # meters per nanosecond
    x = app.xs
    y = app.ys
    T = [None]*len(app.anchors)
    for (id, stamp) in timestamps:
        T[id] = stamp
    tau = [None]*len(app.anchors) #all based on reference anchor 0
    for id, t in enumerate(T):
        tau[id] = t - T[0]
        if tau[id]==0: tau[id] = 1*10**-9
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
    justTimeStamps = list(map(lambda x: (x[1], x[3]), simulatedData))

    x, y = gridToCoord(app.tag.row, app.tag.col)
    linX, linY = linearLocalization(app, justTimeStamps)
    nLinX, nLinY = nonLinearLocalization(app, justTimeStamps)
    filtX, filtY = extendedKalmanEst(app, justTimeStamps)
    if app.isCollecting:
        app.realLocs.append((x, y))
        app.linEstLocs.append((linX, linY))
        app.nonLinEstLocs.append((nLinX, nLinY))
        app.filterEstLocs.append((filtX, filtY))

        print("\nREPORT:")
        print(f"Actual:", app.realLocs[-1][0], app.realLocs[-1][1])
        print(f"Linear:", app.linEstLocs[-1][0], app.linEstLocs[-1][1])
        print(f"Non-Linear:", app.nonLinEstLocs[-1][0], app.nonLinEstLocs[-1][1])
        print(f"Extended Kalman Filter:", app.filterEstLocs[-1][0], app.filterEstLocs[-1][1])
        print("End Report:\n")


def appStarted(app):
    app.timerDelay = 1000//PULSE_FREQ
    app.isCollecting = False
    app.margin = 25
    app.cols = 100//FEET_IN_GRID # 100 feet court width
    app.rows = 50//FEET_IN_GRID  # 50 feet court height
    app.tag = Tag(app.rows//2, app.cols//2, "Player 1")
    app.anchors = []
    app.anchors.append(Anchor(0, 0, 0))
    app.anchors.append(Anchor(app.rows-1, 0, 1))
    app.anchors.append(Anchor(0, app.cols-1, 2))
    app.anchors.append(Anchor(app.rows-1, app.cols-1, 3))
    app.anchors.append(Anchor(0, app.cols//2, 4))
    app.anchors.append(Anchor(app.rows-1, app.cols//2, 5))
    global ANCHORS
    ANCHORS = [None]*len(app.anchors)
    app.xs = [None]*len(app.anchors)
    app.ys = [None]*len(app.anchors)
    for anchor in app.anchors:
        app.xs[anchor.id], app.ys[anchor.id] = gridToCoord(anchor.row, anchor.col)
        ANCHORS[anchor.id] = (app.xs[anchor.id], app.ys[anchor.id])

    app.realLocs = []
    app.linEstLocs = []
    app.nonLinEstLocs = []
    app.filterEstLocs = []
    # app.court = app.loadImage('https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Basketball_court_fiba.svg/440px-Basketball_court_fiba.svg.png').transpose(Image.ROTATE_90).resize((1000,500))
    # app.court = app.loadImage('https://raw.githubusercontent.com/savvastj/nbaPlayerTracking/master/fullcourt.png').resize((1000,500))
    app.court = app.loadImage('decolored-court.png').transpose(Image.ROTATE_90).resize((app.width-2*app.margin,app.height-2*app.margin))
    initFilter(app)
    
def keyPressed(app, event):
    if (event.key == 'Up'):      app.tag.row -= 1
    elif (event.key == 'Down'):  app.tag.row += 1
    elif (event.key == 'Left'):  app.tag.col -= 1
    elif (event.key == 'Right'): app.tag.col += 1
    elif (event.key == 'Space'): app.isCollecting = not app.isCollecting

def timerFired(app):
    runLocalization(app)

def rmse(errors):
    return np.sqrt(np.mean(errors**2))


def appStopped(app):
    #create error reports after app is closed
    print("*"*40, "\n"+"Error Report:")
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
    x = np.arange(1, len(linErrs)+1)
    linErrs = np.array(linErrs)
    nonLinErrs = np.array(nonLinErrs)
    filterErrs = np.array(filterErrs)
    linRMSE = rmse(linErrs)
    nonLinRMSE = rmse(nonLinErrs)
    filterRMSE = rmse(filterErrs)

    plt.plot(x, linErrs, color=linColor, marker='o', label="Linear Error")
    plt.plot(x, nonLinErrs, color=nonLinColor, marker='o', label="Non-linear Error")
    plt.plot(x, filterErrs, color=filterColor, marker='o', label="Kalman Filter Error")
    plt.legend()

    print("Lin RMSE:", linRMSE)
    print("nonLin RMSE:", nonLinRMSE)
    print("filter RMSE:", filterRMSE)
    print("nonLin / filter RMSE:", nonLinRMSE/filterRMSE)
    print("END Report", "\n"+"*"*40)

    plt.show()

def drawX(canvas, cX, cY, w, color):
    x0, y0, x1, y1, x2, y2, x3, y3 = cX-w, cY-w, cX+w, cY-w, cX-w, cY+w, cX+w, cY+w
    canvas.create_line(x0, y0, x3, y3, fill=color, width=3)
    canvas.create_line(x2, y2, x1, y1, fill=color, width=3)

def redrawAll(app, canvas):
    canvas.create_image(app.width//2, app.height//2, image=ImageTk.PhotoImage(app.court))
    canvas.create_text(app.width//2, app.margin//2, text=f"isCollecting:{app.isCollecting}")

    for anchor in app.anchors:
        (x0, y0, x1, y1) = getCellBounds(app, anchor.row, anchor.col)
        canvas.create_rectangle(x0, y0, x1, y1, fill=anchor.color)
        canvas.create_text((x0+x1)/2, (y0+y1)//2, text=f'{anchor.id}')

    # draw tags
    (x0, y0, x1, y1) = getCellBounds(app, app.tag.row, app.tag.col)
    r = min(x1-x0, y1-y0)/2
    cX, cY = (x0+x1)/2, (y0+y1)/2
    canvas.create_oval(cX-r, cY-r, cX+r, cY+r, fill=None, outline=app.tag.color, width = 3)
    r = min(x1-x0, y1-y0)/4
    
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



runApp(width=1550, height=800)