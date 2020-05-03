import csv
fileName = "0_7CMA-100P-10000R-1000Q-1.45Smooth-4Anch-1.5nsNoise"
with open(f"nba_test_logs/{fileName}.txt", "r", newline='') as f:
    cR = csv.reader(f)
    rmses = list(map(lambda x: float(x[0]), cR))
    print(round(sum(rmses)/len(rmses), 4), len(rmses))
