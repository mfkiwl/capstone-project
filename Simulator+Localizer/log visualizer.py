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
pp = pprint.PrettyPrinter()
ANCHORS = None 

##DRAW PARAMETERS#########
realColor = 'black'
linColor = 'purple'
hypColor = 'green'
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
    if WITH_NOISE:
        desc = f"{len(ANCHORS)}Anch-{NOISE_STD_DEV}nsNoise-{PULSE_FREQ}Freq-{pathDesc}"
    else:
        desc = f"{len(ANCHORS)}Anch-noNoise-{PULSE_FREQ}Freq-{pathDesc}"
    return desc

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

def appStarted(app):
    app.logPath = app.loadFilePath()
    print(app.logPath)
    app.margin = 25
    # app.cols = 100//FEET_IN_GRID # 100 feet court width
    # app.rows = 50//FEET_IN_GRID  # 50 feet court height

    app.data = dict()
    with open(app.logPath, 'r') as f:
        cR = csv.DictReader(f)
        for r in cR:
            app.data[int(r["Sample_idx"])] = r

    app.drawReal = app.getUserInput("Draw Real Locations? (y/n)") == 'y'
    app.drawLinear = app.getUserInput("Draw Linear Estimation? (y/n)") == 'y'
    app.drawHyper = app.getUserInput("Draw Hyperbolic Estimation? (y/n)") == 'y'
    app.drawFilter = app.getUserInput("Draw Kalman Filtered Estimation? (y/n)") == 'y'

    app.court = app.loadImage('https://i.imgur.com/YBcbBFq.png').transpose(Image.ROTATE_90).resize((app.width-2*app.margin,app.height-2*app.margin))
    
def keyPressed(app, event): pass
    
def timerFired(app):
    pass

def appStopped(app):pass

def drawX(canvas, cX, cY, w, color):
    x0, y0, x1, y1, x2, y2, x3, y3 = cX-w, cY-w, cX+w, cY-w, cX-w, cY+w, cX+w, cY+w
    canvas.create_line(x0, y0, x3, y3, fill=color, width=3)
    canvas.create_line(x2, y2, x1, y1, fill=color, width=3)

def redrawAll(app, canvas):
    canvas.create_image(app.width//2, app.height//2, image=ImageTk.PhotoImage(app.court))
    
    for idx in range(1, len(app.data.values())):
        if app.drawReal:
            prevX, prevY = metersToPixel(app, float(app.data[idx-1]["realX"]), float(app.data[idx-1]["realY"]))
            currX, currY = metersToPixel(app, float(app.data[idx]["realX"]), float(app.data[idx]["realY"]))
            canvas.create_line(prevX, prevY, currX, currY, fill=realColor, activefill="red", width=4)
            # canvas.create_text(prevX, prevY, text=app.data[idx-1]["Sample_idx"])
        if app.drawLinear:
            prevX, prevY = metersToPixel(app, float(app.data[idx-1]["linEstX"]), float(app.data[idx-1]["linEstY"]))
            currX, currY = metersToPixel(app, float(app.data[idx]["linEstX"]), float(app.data[idx]["linEstY"]))
            canvas.create_line(prevX, prevY, currX, currY, fill=linColor, activefill="red")
        if app.drawHyper:
            prevX, prevY = metersToPixel(app, float(app.data[idx-1]["hypEstX"]), float(app.data[idx-1]["hypEstY"]))
            currX, currY = metersToPixel(app, float(app.data[idx]["hypEstX"]), float(app.data[idx]["hypEstY"]))
            canvas.create_line(prevX, prevY, currX, currY, fill=hypColor, activefill="red")
        if app.drawFilter:
            prevX, prevY = metersToPixel(app, float(app.data[idx-1]["filtEstX"]), float(app.data[idx-1]["filtEstY"]))
            currX, currY = metersToPixel(app, float(app.data[idx]["filtEstX"]), float(app.data[idx]["filtEstY"]))
            canvas.create_line(prevX, prevY, currX, currY, fill=filterColor, activefill="red")

runApp(width=1550, height=800)