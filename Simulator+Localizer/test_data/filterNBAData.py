import pickle
import csv
import pandas
import pprint

pp = pprint.PrettyPrinter(indent=2)
pprint = pp.pprint
import_headers = ["event_id", "game_id", "game_date", "quarter", "timestamp", "game_clock",
                    "shot_clock", "team_id", "player_id", "x_loc", "y_loc", "radius"]

export_headers = ["adjusted_time", "player_id", "x_loc", "y_loc"]

steph = 201939
max_clock = 720.0*4
sample_interval = 0.1 #seconds

data = pickle.load(open("0021500003-NOPatGSW-2015-10-27.pickle", "rb"))
timedData = []

for moment in data:
    if moment[8]!=steph: continue
    quarter, game_clock = moment[3], moment[5]
    adjustedTime = (4-quarter)*720.0 + game_clock
    timedData.append([round(adjustedTime,2), moment[8], moment[9], moment[10]])

timedData.sort(key=lambda x: x[0], reverse=True)
# pprint(timedData[:5])

finalData = []
clock = max_clock
for moment in timedData:
    if moment[0] < clock:
        finalData.append(moment)
        clock -= sample_interval

with open("stephDownSampled.csv", "w+") as f:
    cW = csv.writer(f)
    cW.writerow(export_headers)
    for row in finalData:
        cW.writerow(row)


# df = pandas.DataFrame(data, columns=movement_headers)
# # pprint(data[:10])
# df = df.filter(items=["quarter", "game_clock", "player_id", "x_loc", "y_loc"])
# print(df.head(5))