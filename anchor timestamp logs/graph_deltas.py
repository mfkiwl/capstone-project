from matplotlib import pyplot as plt
import numpy as np
import sys

'''
call from command line as:
    python graph_deltas.py [logfile.txt,logfile2.txt,logfile3.txt] name_of_X_variable_in_logfile name_of_Y_variable_in_logfile
notes:
    if there's only one logfile, don't pass it in brackets: 
        i.e. python graph_deltas.py logfile.txt "name_of_X_variable_in_logfile" "name_of_Y_variable_in_logfile"
    X_variable is assumed to be an integer
    Y_variable is assumed to be a float
    we assume that each logfile contains THE SAME NUMBER OF LOGGED FRAMES
    we assume that the values of each variable are separated from their names by exactly one colon.
    there can be whitespace after the colon, but we assume that one colon is the last non-whitespace char before the variable value
        i.e. reception_#: 13
    Each ROW in the variableY array contains the Y values from ONE log file
'''
def main(filestring,variableX, variableY):
    list_x = list()
    list_y = list()
    print("\ncollecting", variableY, "!\n")

    ### parse filestring into a list of files
    if filestring.startswith("["):
        files = filestring[1:-1].split(",")
    else: files = [filestring]

    ### parse the first file, extract its values, and use them to initialize the variable arrays
    with open(files[0], 'r') as fh:
        print("opening file:" + files[0])
        for line in fh:
            if line.startswith(variableX):
                vX = line.split(":")[1]
                list_x.append(int(vX))
            if line.startswith(variableY):
                vY = line.split(":")[1]
                list_y.append(float(vY))

    x = np.empty([ len(files), len(list_x) ])
    x[0] = np.asarray(list_x)
    y = np.empty([ len(files), len(list_y)])
    y[0] = np.asarray(list_y)


    ### parse each subsequent file, extract their values & append them to subsequent rows in the variable array
    for filename in files[1:]:
        print("opening file:" + filename)
        list_x = []
        list_y = []
        with open(filename, 'r') as fh:
            for line in fh:
                if line.startswith(variableX):
                    vX = line.split(":")[1]
                    list_x.append(int(vX))
                if line.startswith(variableY):
                    vY = line.split(":")[1]
                    list_y.append(float(vY))
        x[files.index(filename)] = np.asarray(list_x)
        y[files.index(filename)] = np.asarray(list_y)

    # calculate the variable Y deltas using the DIFF operator
    # remove all Y deltas less than 0 (caused by rollover)
    delta_x = np.diff(x,axis=1)
    delta_y = np.diff(y,axis=1)
    delta_x = delta_x [delta_y >= 0]
    delta_y = delta_y [delta_y >= 0]
    delta_y_diffs = np.diff(delta_y,axis=0)

    print("dimensions of x:" + str(x.shape))
    print("dimensions of y:" + str(y.shape))
    print("dimensions of delta_x:" + str(delta_x.shape))
    print("dimensions of delta_y:" + str(delta_y.shape))
    print("dimensions of delta_y_diffs:" + str(delta_y_diffs.shape))
    
    mean_delta_diff = np.mean(delta_y_diffs)
    print("for",variableY, "the mean delta difference is", str(mean_delta_diff))

'''
    # Plot variableY
    print("graphing", variableY, "...\n")
    for i in range(y.shape[0]):
        plt.scatter(x[i],y[i])
    plt.xlabel(variableX)
    plt.ylabel(variableY) 
    plt.show()

    # Plot the delta of variableY
    print("graphing the delta of", variableY, "...\n")
    for i in range(delta_y.shape[0]):
        plt.scatter(delta_x[i],delta_y[i])
    plt.xlabel(variableX)
    plt.ylabel("delta " + variableY) 
    plt.show()

    # Plot the delta of variableY
    print("graphing the differences in deltas of", variableY, "...\n")
    plt.scatter(delta_x[0],delta_y_diffs)
    plt.xlabel(variableX)
    plt.ylabel("differences in delta" + variableY)
    plt.show()

'''

# Run the function.
files = sys.argv[1]
variableX = sys.argv[2]
variableY = sys.argv[3]
main(files,variableX,variableY)