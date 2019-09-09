import random
from argparse import ArgumentParser
import numpy as np
import copy
import json
import matplotlib.pyplot as plt

"""
the type of each VM in a NS is uniform distribution
"""

"""
maybe要調的變數:
    NS:
        VNF的location set(分散程度)
        VNF的type
        VNF數目
        budget(要不要和VNF數目或資源需求量呈正相關)
        latency(其實不太重要的東西,可以和VNF數目呈現正相關)
    ESP:
        server數目感覺就每個location各有一個
        server的資源量
        回傳的latency
        server個資源的cost: 可以分成三種不同的類型


"""
# Shared
VM_TYPE = ["MEDIUM", "LARGE", "XLARGE", "XXLARGE"]
RESOURCE_OF_VM_TYPE = {"MEDIUM": {"cpu": 1, "memory": 3.75, "storage": 4},
                       "LARGE": {"cpu": 2, "memory": 7.5, "storage": 32},
                       "XLARGE": {"cpu": 4, "memory": 15, "storage": 80},
                       "XXLARGE": {"cpu": 8, "memory": 30, "storage": 160}
                       }

# NS side
NUM_OF_LOCATION = 5
MEAN_OF_NUM_OF_VNF = 10
# VNF structure: ["type": string,"location": list]

# ESP side
MEAN_OF_NUM_OF_CORE = 30
MEAN_OF_NUM_OF_MEMORY = 300
MEAN_OF_NUM_OF_STORAGE = 600
SD_OF_NUM_OF_CORE = 10
SD_OF_NUM_OF_MEMORY = 50
SD_OF_NUM_OF_STORAGE = 100

MEAN_OF_PRICE_OF_CORE = 20
SD_OF_PRICE_OF_CORE = 5

MEAN_OF_PRICE_OF_MEMORY = 10
SD_OF_PRICE_OF_MEMORY = 2

MEAN_OF_PRICE_OF_STORAGE = 5
SD_OF_PRICE_OF_STORAGE = 1

MEAN_SD_COST = {"cpu": (MEAN_OF_PRICE_OF_CORE, SD_OF_PRICE_OF_CORE),
                "memory": (MEAN_OF_PRICE_OF_MEMORY, SD_OF_PRICE_OF_MEMORY),
                "storage": (MEAN_OF_PRICE_OF_STORAGE, SD_OF_PRICE_OF_STORAGE)}


"""
COST_OF_TYPE_OF_RESOURCE = {"cpu": {"1":(42,0),
                                    "2":(50,10),
                                    "3":(100,20)},
                            "memory": {"1":(50,10),
                                       "2":(0,0),
                                       "3":(1,1)},
                            "storage": {"1":(10,10),
                                        "2":(20,20),
                                        "3":(50,50)}
                            }
"""
COST_OF_TYPE_OF_RESOURCE = {"cpu": [42, 52, 64, 75, 86],
                            "memory": [3.7, 4.3, 5.1, 6.4, 7.0],
                            "storage": [0.05, 0.028, 0.033, 0.04, 0.08]
                            }


def argParse():
    parser = ArgumentParser()
    parser.add_argument("-N", help="number of data", dest="N",
                        default=50)
    parser.add_argument("-n", help="number of network service",
                        dest="n", default=10)
    parser.add_argument("-m", help="number of ESP", dest="m",
                        default=5)
    args = parser.parse_args()
    return args


def randomGeneratePositiveNumber(mean, sd):
    temp = int(np.random.normal(mean, sd, 1))
    while temp < 1:
        temp = int(np.random.normal(mean, sd, 1))
    return temp


def createNSList(n):
    NSList = []
    for j in range(n):
        # VNF數目
        numOfVnf = random.choice([i for i in range(4, 11)])
        vnfList = []
        for k in range(numOfVnf):
            # VNF的type和location set
            vmType = np.random.choice(VM_TYPE, 1, p=[(8/15),(4/15),(2/15),(1/15)])[0]
            nOfLocation = random.choice([i for i in range(1,4)])
            locationSet = random.sample([i for i in range(NUM_OF_LOCATION)], k=nOfLocation)
            vnfList.append(dict(zip(("type", "location"), (vmType, locationSet))))
        # budget
        cost = 0
        for vnf in vnfList:
            for resource, amount in RESOURCE_OF_VM_TYPE[vnf["type"]].items():
                cost += randomGeneratePositiveNumber(MEAN_SD_COST[resource][0], MEAN_SD_COST[resource][1]) * amount

        budget = cost * ((random.randint(5,25))/100 + 1) + int(np.random.normal(50,25,1))
        # latency
        if bool(np.random.choice([True, False], 1, p=[0.7, 0.3])[0]) is True:
            latency = random.choice([i for i in range(20, 100)])
        else:
            latency = None
        ns = dict(zip(("value", "latency", "vnfInfo"), (budget, latency, vnfList)))

        NSList.append(copy.deepcopy(ns))
    return NSList


def createESPList(m):
    ESPList = []
    for i in range(m):
        locations = [i for i in range(NUM_OF_LOCATION)]
        random.shuffle(locations)

        numOfServer = NUM_OF_LOCATION

        serverList = []
        for j in range(numOfServer):
            # cost
            cost = {"cpu": 0, "memory": 0, "storage": 0}
            cost["cpu"] = randomGeneratePositiveNumber(MEAN_SD_COST["cpu"][0], MEAN_SD_COST["cpu"][1])
            cost["memory"] = randomGeneratePositiveNumber(MEAN_SD_COST["memory"][0], MEAN_SD_COST["memory"][1])
            cost["storage"] = randomGeneratePositiveNumber(MEAN_SD_COST["storage"][0], MEAN_SD_COST["storage"][1])
            # resource
            resources = {"cpu": 0, "memory": 0, "storage": 0}
            resources["cpu"] = randomGeneratePositiveNumber(MEAN_OF_NUM_OF_CORE, SD_OF_NUM_OF_CORE)
            resources["memory"] = randomGeneratePositiveNumber(MEAN_OF_NUM_OF_MEMORY, SD_OF_NUM_OF_MEMORY)
            resources["storage"] = randomGeneratePositiveNumber(MEAN_OF_NUM_OF_STORAGE, SD_OF_NUM_OF_STORAGE)
            # server location
            location = locations.pop()

            server = dict(zip(("location", "resources", "cost"), (location, resources, cost)))
            serverList.append(copy.deepcopy(server))
        ESPList.append(serverList)
    return ESPList


def Main():
    # numOfVnf
    args = argParse()
    data = {}

    for i in range(int(args.N)):
        # create NSs
        NSList = createNSList(int(args.n))
        # create ESPs
        ESPList = createESPList(int(args.m))
        data[str(i)] = dict(zip(("NSList", "ESPList"), (NSList, ESPList)))

    filename = "N"+str(args.N)+"n"+str(args.n)+"m"+str(args.m)+".json"
    print(filename)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)



if __name__ == '__main__':
    Main()
