from Simulator import Simulator
import json
import numpy as np
import scipy.stats as st

table = []
format_specifier = ""
header = ""
input_file = open('Inputs.json', )
input_data = json.load(input_file)
# other_metrics=[]

# client_list = [1, 15, 30, 60, 90, 120, 150, 160, 180, 200, 220, 240, 260, 280, 300]
for noOfClients in range(1, 301):
    li = []
    # print("For clients " + str(noOfClients))
    li.append(noOfClients)
    if noOfClients == 1:
        format_specifier = format_specifier + "%d"
        header += "of clients"

    avg_throughput = 0
    avg_utilization = 0
    avg_droprate = 0
    avg_badput = 0
    sample_total = 0
    for run in range(input_data["noOfRuns"]):
        simulator = Simulator(noOfCores=input_data["noOfCores"], noOfThreads=input_data["noOfThreads"],
                              buffSize=input_data["buffSize"], noOfClients=noOfClients,
                              thinkTime=input_data["thinkTime"],
                              simulationTIme=input_data["simulationTIme"],
                              timeQuantum=input_data["timeQuantum"],
                              contextSwitchOverhead=input_data["contextSwitchOverhead"],
                              meanServiceTime=input_data["meanServiceTime"], meanTimeout=input_data["meanTimeout"],
                              servTimeDist=input_data["serviceTimeDistribution"], debug=input_data["debug"])

        simulator.run_simulation()

        li.append(simulator.metrics.responseTime)
        avg_throughput += simulator.metrics.throughPut
        avg_utilization += simulator.metrics.utilization
        avg_droprate += simulator.metrics.dropRate
        avg_badput += simulator.metrics.badput
        sample_total += simulator.metrics.responseTime
        if noOfClients == 1:
            format_specifier = format_specifier + ",%f"
            header += ",Run" + str(run + 1)

    sample_mean = sample_total / input_data["noOfRuns"]
    # print("Sample Mean = " + str(sample_mean))
    sample_diff = 0
    for i in range(1, input_data["noOfRuns"] + 1):
        sample_diff += (li[i] - sample_mean) ** 2
    sample_var = sample_diff / (input_data["noOfRuns"] - 1)
    # print("Sample Variance = " + str(sample_var))
    cond_per = 0.95
    # z((1+beta)/2) = 0.975
    z = st.norm.ppf((1 + cond_per) / 2)
    # print("Z= " + str(z))
    a = sample_mean - z * ((sample_var / input_data["noOfRuns"]) ** 0.5)
    b = sample_mean + z * ((sample_var / input_data["noOfRuns"]) ** 0.5)
    half_width_percentage = (b - a) * 100 / (a + b)
    li.append("(" + str(a) + " - " + str(b) + ")")
    li.append(half_width_percentage)
    li.append(sample_mean)
    li.append(avg_throughput / input_data["noOfRuns"])
    li.append(avg_utilization / input_data["noOfRuns"])
    li.append(avg_droprate / input_data["noOfRuns"])
    li.append(avg_badput / input_data["noOfRuns"])
    table.append(li)

# print(table)
nptable = np.array(table)
# print(nptable)
# print(type(nptable[0, -1]))
format_specifier += ",%s"
header += ",95% confidence_interval,Half_Width_Percentage,Avg_ResponseTime,Avg_Throughput,Avg_Utilization,Avg_Droprate,Avg_Badput"

print("Completed")

np.savetxt("SimulationData.csv", nptable, delimiter=",", fmt="%s", header=header)
