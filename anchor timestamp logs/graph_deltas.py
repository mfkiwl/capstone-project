from matplotlib import pyplot as plt
import numpy as np
import sys

'''
call from command line as:
    python graph_deltas.py logfile.txt "name_of_X_variable_in_logfile" "name_of_Y_variable_in_logfile" "rollover_value"
notes:
    X_variable is assumed to be an integer
    Y_variable is assumed to be a float
    we assume that the values of each variable are separated from their names by exactly one colon.
    there can be whitespace after the colon, 
        but we assume that one colon is the only non-whitespace char before the variable value
    i.e. reception_#: 13
'''
def main(filename,variableX, variableY,rollover=float(17.2)):
    list_x = list()
    list_y = list()
    print("collecting", variableY, "!\n")
    with open(filename, 'r') as fh:
        for line in fh:
            if line.startswith(variableX):
                vX = line.split(":")[1]
                list_x.append(int(vX))
            if line.startswith(variableY):
                vY = line.split(":")[1]
                list_y.append(float(vY))

    print("done collecting", variableY, "!\n")
    print("calculating ")
    x = np.asarray(list_x)
    y = np.asarray(list_y)

    delta_y = np.ediff1d(y)
    #delta_y[delta_y < 0] += rollover
    delta_y = delta_y [delta_y >= 0] # eliminate rollover

    # Plot variableY
    print("graphing", variableY, "...\n")
    plt.plot(x,y,"ob")
    plt.xlabel(variableX)
    plt.ylabel(variableY) 
    plt.show()

    # Plot the delta of variableY
    print("graphing the delta of", variableY, "...\n")
    #plt.plot(x[:-1],delta_y,"ob")
    plt.plot(delta_y,"ob")
    plt.xlabel(variableX)
    plt.ylabel("delta " + variableY) 
    plt.title("average delta = " + str(np.average(delta_y)) + " " + variableY.split("_")[-1])
    plt.show()

    # Calculate the standard deviation of variableY
    stDev = np.std(delta_y)
    print("standard deviation of delta",variableY, "=",stDev,variableY.split("_")[-1],"\n")

# Run the function.
filename = sys.argv[1]
variableX = sys.argv[2]
variableY = sys.argv[3]
if len(sys.argv) > 4:
    rollover = sys.argv[4]
    if (float(rollover) > 17.2):
        rollover = int(rollover)
    else:
        rollover = float(rollover)
    main(filename,variableX,variableY,rollover)
else:
    main(filename,variableX,variableY)