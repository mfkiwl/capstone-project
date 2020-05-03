from cmu_112_graphics import * 
import time
import math
import pprint
import csv
from basketball_mapping import *
pp = pprint.PrettyPrinter()
ANCHORS = None 

##DRAW PARAMETERS#########
realColor = 'black'
linColor = 'purple'
hypColor = 'green'
filterColor = 'red'
draw_sample_window = 200
window_shift = 100
color_gradient = 255/draw_sample_window
##################################

def appStarted(app):
    app.logPath = app.loadFilePath()
    print(app.logPath)
    app.margin = APP_MARGIN
    # app.cols = 100//FEET_IN_GRID # 100 feet court width
    # app.rows = 50//FEET_IN_GRID  # 50 feet court height

    app.data = dict()
    with open(app.logPath, 'r') as f:
        cR = csv.DictReader(f)
        for r in cR:
            app.data[int(r["Sample_idx"])] = r
    app.currSample = 0
    app.drawLinear = app.drawHyper = app.drawFilter = app.drawVelocity = False
    app.drawReal = app.getUserInput("Draw Real Locations? (y/n)") == 'y'
    # if "velX" in app.data[1].keys():
    #     app.drawVelocity = app.getUserInput("Draw Real Velocities? (y/n)") == 'y'
    # if "linEstX" in app.data[1].keys():
    #     app.drawLinear = app.getUserInput("Draw Linear Estimation? (y/n)") == 'y'
    # if "hypEstX" in app.data[1].keys():
    #     app.drawHyper = app.getUserInput("Draw Hyperbolic Estimation? (y/n)") == 'y'
    if "filtEstX" in app.data[1].keys():
        app.drawFilter = app.getUserInput("Draw Kalman Filtered Estimation? (y/n)") == 'y'

    app.court = app.loadImage('https://i.imgur.com/YBcbBFq.png').transpose(Image.ROTATE_90).resize((app.width-2*app.margin,app.height-2*app.margin))
    
def keyPressed(app, event):
    if event.key=="Left":
        app.currSample = max(0, app.currSample-window_shift)
    if event.key=="Right":
        app.currSample = min(len(app.data.values())-2, app.currSample+window_shift)
    
def timerFired(app):
    pass

def appStopped(app):pass

def redrawAll(app, canvas):
    canvas.create_image(app.width//2, app.height//2, image=ImageTk.PhotoImage(app.court))
    canvas.create_text(app.width//2, app.margin//2, text=app.logPath)
    canvas.create_text(app.width//2, app.height-app.margin//2, text=str((app.currSample, app.currSample+draw_sample_window)))
    
    for i, idx in enumerate(range(1+app.currSample, min(len(app.data.values()), 1+app.currSample+draw_sample_window))):
        if app.drawReal:
            prevX, prevY = meterToPixel(app, float(app.data[idx-1]["realX"]), float(app.data[idx-1]["realY"]))
            currX, currY = meterToPixel(app, float(app.data[idx]["realX"]), float(app.data[idx]["realY"]))
            blue_gradient = rgbString(0, 0, i*color_gradient)
            canvas.create_line(prevX, prevY, currX, currY, fill=blue_gradient, activefill="red", width=4)
            # canvas.create_text(prevX, prevY, text=app.data[idx-1]["Sample_idx"])
        if app.drawLinear:
            prevX, prevY = meterToPixel(app, float(app.data[idx-1]["linEstX"]), float(app.data[idx-1]["linEstY"]))
            currX, currY = meterToPixel(app, float(app.data[idx]["linEstX"]), float(app.data[idx]["linEstY"]))
            canvas.create_line(prevX, prevY, currX, currY, fill=linColor, activefill="red")
        if app.drawHyper:
            prevX, prevY = meterToPixel(app, float(app.data[idx-1]["hypEstX"]), float(app.data[idx-1]["hypEstY"]))
            currX, currY = meterToPixel(app, float(app.data[idx]["hypEstX"]), float(app.data[idx]["hypEstY"]))
            canvas.create_line(prevX, prevY, currX, currY, fill=hypColor, activefill="red")
        if app.drawFilter:
            prevX, prevY = meterToPixel(app, float(app.data[idx-1]["filtEstX"]), float(app.data[idx-1]["filtEstY"]))
            currX, currY = meterToPixel(app, float(app.data[idx]["filtEstX"]), float(app.data[idx]["filtEstY"]))
            yellow_gradient = rgbString(255, i*color_gradient, 0)
            canvas.create_line(prevX, prevY, currX, currY, fill=filterColor, activefill="green", width = 2)

runApp(width=APP_WIDTH, height=APP_HEIGHT)