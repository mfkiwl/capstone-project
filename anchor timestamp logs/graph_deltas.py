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

def reject_outliers(data, m=2):
    return data[abs(data - np.mean(data)) < m * np.std(data)]

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
    delta_x = np.diff(x,axis=1)
    delta_y = np.diff(y,axis=1)
    # delta_x = delta_x [delta_y >= 0]
    # delta_y = delta_y [delta_y >= 0]
    delta_y_diffs = np.diff(delta_y,axis=0)
    y_diffs = np.diff(y,axis=0)

    print("dimensions of x:" + str(x.shape))
    print("dimensions of y:" + str(y.shape))
    print("dimensions of delta_x:" + str(delta_x.shape))
    print("dimensions of delta_y:" + str(delta_y.shape))
    print("dimensions of delta_y_diffs:" + str(delta_y_diffs.shape))
    print("dimensions of y_diffs:" + str(y_diffs.shape))
    
    delta_y_diffs = reject_outliers(delta_y_diffs, m=1)

    # find median of calibration values
    calib_len = 100
    y_diffs_calibration = y_diffs[0,:calib_len]
    print("dimensions of y_diffs_calibration: {}".format(y_diffs_calibration.shape))
    y_diffs_calibration_median = np.median(y_diffs_calibration)

    # subtract calibration median 
    median_cutoff = 2
    y_diffs = y_diffs[0,calib_len:]
    print("dimensions of post-calibration y_diffs: {}".format(y_diffs.shape))
    if (abs(y_diffs_calibration_median) >= median_cutoff):
        print("y_diffs_calibration_median: {}".format(y_diffs_calibration_median))
        y_diffs = y_diffs - y_diffs_calibration_median
        print("to compensate for median, y_diffs subtracted by {}".format(y_diffs_calibration_median))
    y_diffs = reject_outliers(y_diffs, m=1)

    dist = 280

    print("Stats of Direct Difference in Reception Timestamps between Anchors, for {}: Mean = {}, Median = {}, St. Dev = {}"
    .format(variableY,np.mean(y_diffs), np.median(y_diffs), np.std(y_diffs)))

    print("Stats of Difference in Timestamp Deltas between Anchors, for {}: Mean = {}, Median = {}, St. Dev = {}"
    .format(variableY,np.mean(delta_y_diffs), np.median(delta_y_diffs), np.std(delta_y_diffs)))

    print("graphing the corresponding difference between deltas of reception timestamps in", variableY, "...\n")
    plt.scatter(np.arange(delta_y_diffs.shape[0]),delta_y_diffs)
    plt.xlabel(variableX)
    plt.ylabel("difference in corresponding delta of receptions" + variableY) 
    plt.title("At " + str(dist) + " CM Apart, Differences of Deltas in Corresponding Reception Timestamp Between Anchors \n in " 
        + variableY + " over " + variableX)
    plt.show()

    print("graphing the direct difference between ", variableY, "...\n")
    plt.scatter(np.arange(y_diffs.shape[0]) + y_diffs_calibration.size,y_diffs)
    plt.xlabel(variableX)
    plt.ylabel("difference in direct time of reception in " + variableY) 
    plt.title("At " + str(dist) + " CM Apart, Direct Difference in Corresponding Reception Timestamps Between Anchors \n in "
        + variableY + " over " + variableX)
    plt.show()


# Run the function.
files = sys.argv[1]
variableX = sys.argv[2]
variableY = sys.argv[3]
main(files,variableX,variableY)