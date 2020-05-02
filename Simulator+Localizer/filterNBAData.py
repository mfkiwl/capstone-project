import pickle
import csv
import os
import pprint
import time
from collections import defaultdict
from basketball_mapping import *

pp = pprint.PrettyPrinter(indent=2)
pprint = pp.pprint
import_headers = ["event_id", "game_id", "game_date", "quarter", "timestamp", "game_clock",
                    "shot_clock", "team_id", "player_id", "x_loc", "y_loc", "radius"]

export_headers = ["Sample_idx", "timestamp_ms", "adjusted_game_time", "player_id", "realX", "realY"]

steph = 201939
max_clock = 720.0*4
SAMPLE_INTERVAL = 100 #milliseconds

def getPlayerString(pid):
    return f"{pid}_{players[player]['firstname']}_{players[player]['lastname']}_{players[player]['jersey']}_{players[player]['position']}"
startT = time.time()
gameFile = "0021500003-NOPatGSW-2015-10-27"
data = pickle.load(open(f"test_data/{gameFile}.pickle", "rb"))
players = pickle.load(open("test_data/0_players.pickle", 'rb'))

playerToSamples = defaultdict(lambda: [])

t = time.time()
counter = 0
for moment in data:
    pid = moment[8]
    if pid==-1: continue
    # if pid!=steph: continue
    quarter, game_clock = moment[3], moment[5]
    adjustedTime = (4-quarter)*720.0 + game_clock
    footX, footY = moment[9], moment[10]
    meterX, meterY = footToMeter(footX), footToMeter(footY)
    playerToSamples[pid].append([int(moment[4]%1e10), round(adjustedTime,2), moment[8], round(meterX, 4), round(meterY, 4)])
    counter+=1
    if counter%100000==0:
        # print(f"Processed {counter} moments in {time.time()-t} seconds")
        t = time.time()

for samples in playerToSamples.values():
    samples.sort(key=lambda x: x[0])

t = time.time()
for player, samples in playerToSamples.items():
    downsampledSamples = []
    timestamp = samples[0][0]
    for sample in samples:
        if sample[0] >= timestamp:
            downsampledSamples.append(sample)
            timestamp = sample[0] + SAMPLE_INTERVAL
    playerToSamples[player] = downsampledSamples
    # print(f"Processed {getPlayerString(player)} moments into {len(downsampledSamples)} samples in {time.time()-t} seconds")
    t = time.time()

for player, samples in playerToSamples.items():
    playerString = getPlayerString(player)
    dir = f"test_data/{gameFile}"
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(f"{dir}/{playerString}.csv", "w+", newline='') as f:
        cW = csv.writer(f)
        cW.writerow(export_headers)
        for i, row in enumerate(samples):
            cW.writerow([i]+row)

print(f"DONE. Took {time.time()-startT} seconds")