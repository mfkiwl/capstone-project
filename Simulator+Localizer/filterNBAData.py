import pickle
import csv
import pandas
import pprint
from basketball_mapping import *

pp = pprint.PrettyPrinter(indent=2)
pprint = pp.pprint
import_headers = ["event_id", "game_id", "game_date", "quarter", "timestamp", "game_clock",
                    "shot_clock", "team_id", "player_id", "x_loc", "y_loc", "radius"]

export_headers = ["Sample_idx", "timestamp_ms", "adjusted_game_time", "player_id", "realX", "realY"]

steph = 201939
max_clock = 720.0*4
sample_interval = 100 #milliseconds

data = pickle.load(open("test_data/0021500003-NOPatGSW-2015-10-27.pickle", "rb"))
timedData = []

for moment in data:
    if moment[8]!=steph: continue
    quarter, game_clock = moment[3], moment[5]
    adjustedTime = (4-quarter)*720.0 + game_clock
    footX, footY = moment[9], moment[10]
    meterX, meterY = footToMeter(footX), footToMeter(footY)
    timedData.append([int(moment[4]%1e10), round(adjustedTime,2), moment[8], round(meterX, 4), round(meterY, 4)])

timedData.sort(key=lambda x: x[0])

finalData = []

timestamp = timedData[0][0]
for moment in timedData:
    if moment[0] >= timestamp:
        finalData.append(moment)
        timestamp = moment[0] + sample_interval

with open("test_data/stephDownSampled.csv", "w+", newline='') as f:
    cW = csv.writer(f)
    cW.writerow(export_headers)
    for i, row in enumerate(finalData):
        cW.writerow([i]+row)


# df = pandas.DataFrame(data, columns=movement_headers)
# # pprint(data[:10])
# df = df.filter(items=["quarter", "game_clock", "player_id", "x_loc", "y_loc"])
# print(df.head(5))