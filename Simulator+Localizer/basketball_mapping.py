import math
import numpy as np
##################################
#CONSTANTS#
METERS_IN_FOOT = 0.304800000
FEET_IN_GRID = 1
SPEED_OF_LIGHT = 299702547 # m/s in air
COURT_WIDTH_FEET = 94
COURT_HEIGHT_FEET = 50
APP_HEIGHT = 800
APP_MARGIN = 25
APP_WIDTH = int((800-2*APP_MARGIN)*COURT_WIDTH_FEET/COURT_HEIGHT_FEET+APP_MARGIN*2)
#######################################

def footToMeter(x):
    return x*METERS_IN_FOOT

def meterToFoot(x):
    return x/METERS_IN_FOOT

def rgbString(red, green, blue):
    # Don't worry about how this code works yet.
    return "#%02x%02x%02x" % (int(red), int(green), int(blue))

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
    pixelsInFootW = pixelWidth/COURT_WIDTH_FEET
    pixelsInFootH = pixelHeight/COURT_HEIGHT_FEET
    pixX = x/METERS_IN_FOOT*pixelsInFootW+app.margin
    pixY = y/METERS_IN_FOOT*pixelsInFootH+app.margin
    return (pixX, pixY)

def meterToPixel(app, x, y):
    return metersToPixel(app, x, y)

def footToPixel(app, x, y):
    pixelWidth  = app.width - 2*app.margin
    pixelHeight = app.height - 2*app.margin
    pixelsInFootW = pixelWidth/COURT_WIDTH_FEET
    pixelsInFootH = pixelHeight/COURT_HEIGHT_FEET
    pixX = x*pixelsInFootW+app.margin
    pixY = y*pixelsInFootH+app.margin
    return (pixX, pixY)

def gridToCoord(row, col):
    return gridToMeter(row, col)

def gridToMeter(row, col):
    return ((col * FEET_IN_GRID + FEET_IN_GRID/2) * METERS_IN_FOOT, (row * FEET_IN_GRID + FEET_IN_GRID/2) * METERS_IN_FOOT)

def gridToFoot(row, col):
    return ((col * FEET_IN_GRID + FEET_IN_GRID/2), (row * FEET_IN_GRID + FEET_IN_GRID/2))


def coordToGrid(x, y): #coord to row/col number
    feetX = x/METERS_IN_FOOT
    feetY = y/METERS_IN_FOOT
    return (int(feetY//FEET_IN_GRID), int(feetX//FEET_IN_GRID))

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

def rmse(errors):
    return np.sqrt(np.mean(errors**2))

def drawX(canvas, cX, cY, w, color):
    x0, y0, x1, y1, x2, y2, x3, y3 = cX-w, cY-w, cX+w, cY-w, cX-w, cY+w, cX+w, cY+w
    canvas.create_line(x0, y0, x3, y3, fill=color, width=3)
    canvas.create_line(x2, y2, x1, y1, fill=color, width=3)