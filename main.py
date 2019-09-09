#!/usr/local/bin/python3
import NS
import ESP
import json
import gc
import random
import copy
from argparse import ArgumentParser
import numpy as np
import pandas as pd
import math

# NS format
# NS = {"vnf":[], "value":0, "bids":[], "latency":0}
# ESP format
# ESP = {"server":[]}
# VM type
VMTYPE = {"MEDIUM": {"cpu": 1, "memory": 3.75, "storage": 4},
          "LARGE": {"cpu": 2, "memory": 7.5, "storage": 32},
          "XLARGE": {"cpu": 4, "memory": 15, "storage": 80},
          "XXLARGE": {"cpu": 8, "memory": 30, "storage": 160}}

"""
MEDIUM = {"cpu": 1, "memory": 3.75, "storage": 4}
LARGE = {"cpu": 2, "memory": 7.5, "storage": 32}
XLARGE = {"cpu": 4, "memory": 15, "storage": 80}
XXLARGE = {"cpu": 8, "memory": 30, "storage": 160}
"""
TOTAL_ITERATION = 0

def argParse():
    parser = ArgumentParser()
    parser.add_argument("s", help="strategy: 1 for my, 2 for random")
    parser.add_argument("N", help="number of data")
    parser.add_argument("n", help="number of network service")
    parser.add_argument("m", help="number of ESP")
    args = parser.parse_args()
    return args

def printNSParnter(NSList):
    for NSP in NSList:
        print("\tNS " + NSP.name + " is "+NSP.state+".", end=' ')
        if NSP.partner is not None:
            print("It's parnter is ESP", NSP.partner)
        else:
            print("It doesn't have partner")


def initailizeNS(NSList, ESPList):
    for ns in NSList:
        ns.initialVnfList(VMTYPE)
        for esp in ESPList:
            ns.query(esp)


def randomAlgo(NSList, ESPList):
    for ns in NSList:
        ns.initialVnfList(VMTYPE)
    NSPlay = NSList.copy()

    while len(NSPlay) !=0:
        ns = random.choice(NSPlay)
        NSPlay.remove(ns)
        ESPPlay = ESPList.copy()
        while len(ESPPlay) != 0:
            esp = random.choice(ESPPlay)
            ESPPlay.remove(esp)
            nsName = ns.name
            espName = esp.name
            # chk capacity
            totalCost = 0
            canServe = True

            for vnfName, vnf in ns.vnfList.items():
                price, serverName = esp.calVnfCostAndSatify(vnf)
                if price is None:
                    canServe = False
                    break
                else:
                    vnf.allocatedServerRandom = serverName
                    esp.serverList[serverName].mark(vnf)
                    totalCost += price

            if canServe is False or totalCost > ns.value:
                freeServerList = set()
                for vnfName, vnf in ns.vnfList.items():
                    if vnf.allocatedServerRandom is not None:
                        freeServerList.add(vnf.allocatedServerRandom)
                        vnf.allocatedServerRandom = None
                for serverName in freeServerList:
                    esp.serverList[serverName].delete(ns.name)
                continue

            # calculate latency
            rawDistance = 0
            processingTime = 0
            for i in range(len(ns.vnfList)):
                vnfHere = ns.vnfList[str(i)]
                if i != (len(ns.vnfList)-1):
                    vnfNextHere = ns.vnfList[str(i+1)]
                    if vnfHere.allocatedServerRandom != vnfNextHere.allocatedServerRandom:
                        pointX = (esp.serverList[vnfHere.allocatedServerRandom].geo["x"], esp.serverList[vnfHere.allocatedServerRandom].geo["y"])
                        pointY = (esp.serverList[vnfNextHere.allocatedServerRandom].geo["x"], esp.serverList[vnfNextHere.allocatedServerRandom].geo["y"])
                        rawDistance += math.sqrt((pointX[0]-pointY[0])**2+(pointX[1]-pointY[1])**2)
                VMType = vnfHere.type
                if VMType == "MEDIUM":
                    processingTime += 1
                elif VMType == "LARGE":
                    processingTime += 2
                elif VMType == "XLARGE":
                    processingTime += 4
                elif VMType == "XXLARGE":
                    processingTime += 8

            expectedLatency = int(rawDistance*4) + processingTime

            if ns.latency is not None and ns.latency < expectedLatency:
                freeServerList = set()
                for vnfName, vnf in ns.vnfList.items():
                    if vnf.allocatedServerRandom is not None:
                        freeServerList.add(vnf.allocatedServerRandom)
                        vnf.allocatedServerRandom = None
                for serverName in freeServerList:
                    esp.serverList[serverName].delete(nsName)
                continue

            info = {}
            if totalCost > ns.value:
                print("IMPOSSIBLE")

            payment = (totalCost + ns.value)/2

            assert payment >= totalCost
            info["total needs"] = ns.totalNeeds
            info["total cost"] = totalCost
            info["vnf list"] = ns.vnfList
            info["bid"] = payment
            info["latency"] = ns.latency
            esp.NSInfo[ns.name] = copy.deepcopy(info)
            del info

            # set esp
            esp.acceptList.append(nsName)

            # set ns
            ns.expectedLatency[espName] = expectedLatency
            ns.state = "match"
            ns.partner = espName
            ns.bids[ns.partner] = payment


def randomDA(NSList, ESPList):
    initailizeNS(NSList, ESPList)
    NSPlay = NSList.copy()

    while len(NSPlay) != 0:
        ns = random.choice(NSPlay)
        NSPlay.remove(ns)
        isDeployed = False
        while len(ns.potentialESPList) != 0:
            espName = random.choice(ns.potentialESPList)
            ns.potentialESPList.remove(espName)
            esp = ESPList[int(espName)]
            nsName = ns.name

            ns.bids[espName] = (ns.value+ns.bids[espName])/2
            preResult = esp.acceptOrDenyTemp(nsName, ns.bids[espName])
            if preResult:
                ns.state = "match"
                ns.partner = espName
                isDeployed = True
                break
        if not isDeployed:
            ns.state = "match"
            ns.partner = None


def RA_CHA(NSList, ESPList):
    initailizeNS(NSList, ESPList)
    NSPlay = NSList.copy()

    while len(NSPlay) != 0:
        ns = random.choice(NSPlay)
        NSPlay.remove(ns)
        isDeployed = False
        while len(ns.potentialESPList) != 0:
            espName = random.choice(ns.potentialESPList)
            ns.potentialESPList.remove(espName)
            esp = ESPList[int(espName)]
            ns.bids[espName] = (ns.value+ns.bids[espName])/2
            bid = ns.bids[espName]
            esp.NSInfo[ns.name]["bid"] = bid
            nsList = []
            nsList.append(ns.name)
            for oldNS in esp.acceptList:
                nsList.append(oldNS)

            preResult = esp.CHA(nsList, ns.name)
            if preResult:
                esp.acceptList.append(ns.name)
                ns.state = "match"
                ns.partner = espName
                isDeployed = True
                break
        if not isDeployed:
            ns.state = "match"
            ns.partner = None


def RA_BO(NSList, ESPList):
    initailizeNS(NSList, ESPList)
    NSPlay = NSList.copy()

    while len(NSPlay) != 0:
        ns = random.choice(NSPlay)
        NSPlay.remove(ns)
        isDeployed = False
        while len(ns.potentialESPList) != 0:
            espName = random.choice(ns.potentialESPList)
            ns.potentialESPList.remove(espName)
            esp = ESPList[int(espName)]
            ns.bids[espName] = (ns.value+ns.bids[espName])/2
            bid = ns.bids[espName]
            esp.NSInfo[ns.name]["bid"] = bid
            nsList = []
            nsList.append(ns.name)
            for oldNS in esp.acceptList:
                nsList.append(oldNS)

            preResult = esp.BO(nsList, ns.name)
            if preResult:
                esp.acceptList.append(ns.name)
                ns.state = "match"
                ns.partner = espName
                isDeployed = True
                break
        if not isDeployed:
            ns.state = "match"
            ns.partner = None





def onesideAlgo(NSList, ESPList):
    initailizeNS(NSList, ESPList)
    NSPlay = NSList.copy()
    while len(NSPlay) != 0:

        # NS random choose an ESP to propose
        ns = random.choice(NSPlay)
        if len(ns.potentialESPList) == 0:
            NSPlay.remove(ns)
            continue
        proposedESPName = random.choice(ns.potentialESPList)
        proposedBid = ns.bids[proposedESPName]
        if proposedBid > ns.value:
            ns.potentialESPList.remove(proposedESPName)
            continue
        # ESP decide process
        for _ in ESPList:
            if _.name == proposedESPName:
                esp = _

        preResult = esp.acceptOrDenyTemp(ns.name, proposedBid)

        if preResult is True:
            ns.state = "match"
            ns.partner = esp.name
            NSPlay.remove(ns)
        else:
            result, denyList = esp.tryReallocate(ns.name, proposedBid)
            if result is True:
                assert len(denyList) == len(set(denyList))
                if len(denyList) != 0:
                    for denyNsName in denyList:
                        for otherNS in NSList:
                            if otherNS.name == denyNsName:
                                otherNS.state = "unmatch"
                                otherNS.partner = None
                                NSPlay.append(otherNS)
                                otherNS.bids[esp.name] += 20
                ns.state = "match"
                ns.partner = esp.name
                NSPlay.remove(ns)
            else:
                ns.bids[esp.name] += 20


def CHA_RA(NSList, ESPList):
    initailizeNS(NSList, ESPList)

    NSPlay = NSList.copy()
    while len(NSPlay) != 0:
        ns = random.choice(NSPlay)
        if len(ns.potentialESPList) == 0:
            ns.state = "match"
            ns.partner = None
            NSPlay.remove(ns)
            continue
        espName = random.choice(ns.potentialESPList)
        bid = ns.bids[espName]
        if bid > ns.value:
            ns.potentialESPList.remove(espName)
            continue
        # ESP decide process
        for _ in ESPList:
            if _.name == espName:
                esp = _

        # HERE
        esp.NSInfo[ns.name]["bid"] = bid
        nsList = []
        nsList.append(ns.name)
        for NSName in esp.acceptList:
            nsList.append(NSName)
        preResult, allocation = esp.randomAllocation(nsList, ns.name)

        if preResult is True:
            esp.acceptList.append(ns.name)
            ns.state = "match"
            ns.partner = esp.name
            NSPlay.remove(ns)
        else:
            freeNSList = []
            newNSPrefer = (bid/esp.NSInfo[ns.name]["weight needs"])
            for NSName in esp.acceptList:
                prefer = (esp.NSInfo[NSName]["bid"] /
                          esp.NSInfo[NSName]["weight needs"])
                if prefer <= newNSPrefer:
                    freeNSList.append((prefer, NSName))
            freeNSList.sort()
            restoreNSList = []
            denyNSList = []
            accept = False
            for value, freeName in freeNSList:
                esp.acceptList.remove(freeName)
                restoreNSList.append((value, freeName))
                # delete NS and VNF from server's serveList and serveNSList

                for serverName, server in esp.serverList.items():
                    if freeName in server.serveNSList:
                        server.delete(freeName)

                nsList2 = []
                nsList2.append(ns.name)
                for NSName in esp.acceptList:
                    nsList2.append(NSName)
                preResult, allocation = esp.randomAllocation(nsList2, ns.name)
                if preResult:
                    esp.acceptList.append(ns.name)
                    accept = True
                    break

            if len(restoreNSList) != 0:
                # print("ESP", self.name, "try to restore", restoreNSList)
                restoreNSList.sort()
                restoreNSList.reverse()
                for value, NSName in restoreNSList:
                    nsList3 = []
                    nsList3.append(NSName)
                    for oldNS in esp.acceptList:
                        nsList3.append(oldNS)
                    preResult, allocation = esp.randomAllocation(nsList3, NSName)
                    if preResult:
                        esp.acceptList.append(NSName)
                        continue
                    else:
                        denyNSList.append(NSName)

            if accept:
                if len(denyNSList) != 0:
                    for nsName in denyNSList:
                        for otherNS in NSList:
                            if nsName == otherNS.name:
                                otherNS.state = "unmatch"
                                otherNS.partner = None
                                otherNS.bids[espName] += 20
                                NSPlay.append(otherNS)
                ns.state = "match"
                ns.partner = espName
                NSPlay.remove(ns)
            else:
                ns.bids[espName] += 20


def CHA_CHA(NSList, ESPList):
    initailizeNS(NSList, ESPList)

    NSPlay = NSList.copy()
    while len(NSPlay) != 0:
        ns = random.choice(NSPlay)
        if len(ns.potentialESPList) == 0:
            ns.state = "match"
            ns.partner = None
            NSPlay.remove(ns)
            continue
        espName = random.choice(ns.potentialESPList)
        bid = ns.bids[espName]
        if bid > ns.value:
            ns.potentialESPList.remove(espName)
            continue
        # ESP decide process
        for _ in ESPList:
            if _.name == espName:
                esp = _

        # HERE
        esp.NSInfo[ns.name]["bid"] = bid
        nsList = []
        nsList.append(ns.name)
        for NSName in esp.acceptList:
            nsList.append(NSName)
        preResult, allocation = esp.CHA(nsList, ns.name)

        if preResult is True:
            esp.acceptList.append(ns.name)
            ns.state = "match"
            ns.partner = esp.name
            NSPlay.remove(ns)
        else:
            freeNSList = []
            newNSPrefer = (bid/esp.NSInfo[ns.name]["weight needs"])
            for NSName in esp.acceptList:
                prefer = (esp.NSInfo[NSName]["bid"] /
                          esp.NSInfo[NSName]["weight needs"])
                if prefer <= newNSPrefer:
                    freeNSList.append((prefer, NSName))
            freeNSList.sort()
            restoreNSList = []
            denyNSList = []
            accept = False
            for value, freeName in freeNSList:
                esp.acceptList.remove(freeName)
                restoreNSList.append((value, freeName))
                # delete NS and VNF from server's serveList and serveNSList

                for serverName, server in esp.serverList.items():
                    if freeName in server.serveNSList:
                        server.delete(freeName)

                nsList2 = []
                nsList2.append(ns.name)
                for NSName in esp.acceptList:
                    nsList2.append(NSName)
                preResult, allocation = esp.CHA(nsList2, ns.name)
                if preResult:
                    esp.acceptList.append(ns.name)
                    accept = True
                    break

            if len(restoreNSList) != 0:
                # print("ESP", self.name, "try to restore", restoreNSList)
                restoreNSList.sort()
                restoreNSList.reverse()
                for value, NSName in restoreNSList:
                    nsList3 = []
                    nsList3.append(NSName)
                    for oldNS in esp.acceptList:
                        nsList3.append(oldNS)
                    preResult, allocation = esp.CHA(nsList3, NSName)
                    if preResult:
                        esp.acceptList.append(NSName)
                        continue
                    else:
                        denyNSList.append(NSName)

            if accept:
                if len(denyNSList) != 0:
                    for nsName in denyNSList:
                        for otherNS in NSList:
                            if nsName == otherNS.name:
                                otherNS.state = "unmatch"
                                otherNS.partner = None
                                otherNS.bids[espName] += 20
                                NSPlay.append(otherNS)
                ns.state = "match"
                ns.partner = espName
                NSPlay.remove(ns)
            else:
                ns.bids[espName] += 20


def CHA_BO(NSList, ESPList):
    initailizeNS(NSList, ESPList)

    NSPlay = NSList.copy()
    while len(NSPlay) != 0:
        ns = random.choice(NSPlay)
        if len(ns.potentialESPList) == 0:
            ns.state = "match"
            ns.partner = None
            NSPlay.remove(ns)
            continue
        espName = random.choice(ns.potentialESPList)
        bid = ns.bids[espName]
        if bid > ns.value:
            ns.potentialESPList.remove(espName)
            continue
        # ESP decide process
        for _ in ESPList:
            if _.name == espName:
                esp = _

        # HERE
        esp.NSInfo[ns.name]["bid"] = bid
        nsList = []
        nsList.append(ns.name)
        for NSName in esp.acceptList:
            nsList.append(NSName)
        preResult, allocation = esp.BO(nsList, ns.name)

        if preResult is True:
            esp.acceptList.append(ns.name)
            ns.state = "match"
            ns.partner = esp.name
            NSPlay.remove(ns)
        else:
            freeNSList = []
            newNSPrefer = (bid/esp.NSInfo[ns.name]["weight needs"])
            for NSName in esp.acceptList:
                prefer = (esp.NSInfo[NSName]["bid"] /
                          esp.NSInfo[NSName]["weight needs"])
                if prefer <= newNSPrefer:
                    freeNSList.append((prefer, NSName))
            freeNSList.sort()
            restoreNSList = []
            denyNSList = []
            accept = False
            for value, freeName in freeNSList:
                esp.acceptList.remove(freeName)
                restoreNSList.append((value, freeName))
                # delete NS and VNF from server's serveList and serveNSList

                for serverName, server in esp.serverList.items():
                    if freeName in server.serveNSList:
                        server.delete(freeName)

                nsList2 = []
                nsList2.append(ns.name)
                for NSName in esp.acceptList:
                    nsList2.append(NSName)
                preResult, allocation = esp.BO(nsList2, ns.name)
                if preResult:
                    esp.acceptList.append(ns.name)
                    accept = True
                    break

            if len(restoreNSList) != 0:
                # print("ESP", self.name, "try to restore", restoreNSList)
                restoreNSList.sort()
                restoreNSList.reverse()
                for value, NSName in restoreNSList:
                    nsList3 = []
                    nsList3.append(NSName)
                    for oldNS in esp.acceptList:
                        nsList3.append(oldNS)
                    preResult, allocation = esp.BO(nsList3, NSName)
                    if preResult:
                        esp.acceptList.append(NSName)
                        continue
                    else:
                        denyNSList.append(NSName)

            if accept:
                if len(denyNSList) != 0:
                    for nsName in denyNSList:
                        for otherNS in NSList:
                            if nsName == otherNS.name:
                                otherNS.state = "unmatch"
                                otherNS.partner = None
                                otherNS.bids[espName] += 20
                                NSPlay.append(otherNS)
                ns.state = "match"
                ns.partner = espName
                NSPlay.remove(ns)
            else:
                ns.bids[espName] += 20





def revisedDA(NSList, ESPList):
    total = 0
    initailizeNS(NSList, ESPList)


    while True:
        total += 1
        end = True
        for ns in NSList:
            if ns.state == "unmatch":
                end = False
                espName, bid = ns.ProposeESPAndBid()
                if espName is None:
                    ns.state = "match"
                    ns.partner = None
                    continue
                esp = ESPList[int(espName)]

                preResult = esp.acceptOrDenyTemp(ns.name, bid)
                if preResult:
                    ns.state = "match"
                    ns.partner = espName
                else:
                    result, denyList = esp.tryReallocate(ns.name, bid)
                    if result:
                        if len(denyList) != 0:
                            for nsName in denyList:
                                for otherNS in NSList:
                                    if nsName == otherNS.name:
                                        otherNS.state = "unmatch"
                                        otherNS.partner = None
                                        otherNS.bids[espName] += 20
                        ns.state = "match"
                        ns.partner = espName
                    else:
                        ns.bids[espName] += 20
        if end is True:
            break
    return total

def DA_CHA(NSList, ESPList):
    total = 0
    initailizeNS(NSList, ESPList)

    while True:
        total += 1
        end = True
        for ns in NSList:
            if ns.state == "unmatch":
                end = False
                espName, bid = ns.ProposeESPAndBid()
                if espName is None:
                    ns.state = "match"
                    ns.partner = None
                    continue
                esp = ESPList[int(espName)]

                esp.NSInfo[ns.name]["bid"] = bid
                nsList = []
                nsList.append(ns.name)
                for NSName in esp.acceptList:
                    nsList.append(NSName)
                preResult, allocation = esp.CHA(nsList, ns.name)
                if preResult:
                    esp.acceptList.append(ns.name)
                    ns.state = "match"
                    ns.partner = espName
                else:
                    freeNSList = []
                    newNSPrefer = (bid/esp.NSInfo[ns.name]["weight needs"])
                    for NSName in esp.acceptList:
                        prefer = (esp.NSInfo[NSName]["bid"] /
                                  esp.NSInfo[NSName]["weight needs"])
                        if prefer <= newNSPrefer:
                            freeNSList.append((prefer, NSName))


                    freeNSList.sort()
                    restoreNSList = []
                    denyNSList = []
                    accept = False
                    for value, freeName in freeNSList:
                        esp.acceptList.remove(freeName)
                        restoreNSList.append((value, freeName))
                        # delete NS and VNF from server's serveList and serveNSList

                        for serverName, server in esp.serverList.items():
                            if freeName in server.serveNSList:
                                server.delete(freeName)

                        nsList2 = []
                        nsList2.append(ns.name)
                        for NSName in esp.acceptList:
                            nsList2.append(NSName)
                        preResult, allocation = esp.CHA(nsList, ns.name)
                        if preResult:
                            esp.acceptList.append(ns.name)
                            accept = True
                            break

                    if len(restoreNSList) != 0:
                        # print("ESP", self.name, "try to restore", restoreNSList)
                        restoreNSList.sort()
                        restoreNSList.reverse()
                        for value, NSName in restoreNSList:
                            nsList3 = []
                            nsList3.append(NSName)
                            for oldNS in esp.acceptList:
                                nsList3.append(oldNS)
                            preResult, allocation = esp.CHA(nsList3, NSName)
                            if preResult:
                                esp.acceptList.append(NSName)
                                continue
                            else:
                                denyNSList.append(NSName)

                    if accept:
                        if len(denyNSList) != 0:
                            for nsName in denyNSList:
                                for otherNS in NSList:
                                    if nsName == otherNS.name:
                                        otherNS.state = "unmatch"
                                        otherNS.partner = None
                                        otherNS.bids[espName] += 20
                        ns.state = "match"
                        ns.partner = espName
                    else:
                        ns.bids[espName] += 20
        if end is True:
            break
    return total




def DA_RA(NSList, ESPList):
    total = 0
    initailizeNS(NSList, ESPList)

    while True:
        total += 1
        end = True
        for ns in NSList:
            if ns.state == "unmatch":
                end = False
                espName, bid = ns.ProposeESPAndBid()
                if espName is None:
                    ns.state = "match"
                    ns.partner = None
                    continue
                esp = ESPList[int(espName)]

                esp.NSInfo[ns.name]["bid"] = bid
                nsList = []
                nsList.append(ns.name)
                for NSName in esp.acceptList:
                    nsList.append(NSName)
                preResult, allocation = esp.randomAllocation(nsList, ns.name)
                if preResult:
                    esp.acceptList.append(ns.name)
                    ns.state = "match"
                    ns.partner = espName
                else:
                    freeNSList = []
                    newNSPrefer = (bid/esp.NSInfo[ns.name]["weight needs"])
                    for NSName in esp.acceptList:
                        prefer = (esp.NSInfo[NSName]["bid"] /
                                  esp.NSInfo[NSName]["weight needs"])
                        if prefer <= newNSPrefer:
                            freeNSList.append((prefer, NSName))


                    freeNSList.sort()
                    restoreNSList = []
                    denyNSList = []
                    accept = False
                    for value, freeName in freeNSList:
                        esp.acceptList.remove(freeName)
                        restoreNSList.append((value, freeName))
                        # delete NS and VNF from server's serveList and serveNSList

                        for serverName, server in esp.serverList.items():
                            if freeName in server.serveNSList:
                                server.delete(freeName)

                        nsList2 = []
                        nsList2.append(ns.name)
                        for NSName in esp.acceptList:
                            nsList2.append(NSName)
                        preResult, allocation = esp.randomAllocation(nsList2, ns.name)
                        if preResult:
                            esp.acceptList.append(ns.name)
                            accept = True
                            break

                    if len(restoreNSList) != 0:
                        # print("ESP", self.name, "try to restore", restoreNSList)
                        restoreNSList.sort()
                        restoreNSList.reverse()
                        for value, NSName in restoreNSList:
                            nsList3 = []
                            nsList3.append(NSName)
                            for oldNS in esp.acceptList:
                                nsList3.append(oldNS)
                            preResult, allocation = esp.randomAllocation(nsList3, NSName)
                            if preResult:
                                esp.acceptList.append(NSName)
                                continue
                            else:
                                denyNSList.append(NSName)

                    if accept:
                        if len(denyNSList) != 0:
                            for nsName in denyNSList:
                                for otherNS in NSList:
                                    if nsName == otherNS.name:
                                        otherNS.state = "unmatch"
                                        otherNS.partner = None
                                        otherNS.bids[espName] += 20
                        ns.state = "match"
                        ns.partner = espName
                    else:
                        ns.bids[espName] += 20
        if end is True:
            break
    return total


def DA_BO(NSList, ESPList):
    total = 0
    initailizeNS(NSList, ESPList)

    while True:
        total += 1
        end = True
        for ns in NSList:
            if ns.state == "unmatch":
                end = False
                espName, bid = ns.ProposeESPAndBid()
                if espName is None:
                    ns.state = "match"
                    ns.partner = None
                    continue
                esp = ESPList[int(espName)]

                esp.NSInfo[ns.name]["bid"] = bid
                nsList = []
                nsList.append(ns.name)
                for NSName in esp.acceptList:
                    nsList.append(NSName)
                preResult, allocation = esp.BO(nsList, ns.name)
                if preResult:
                    esp.acceptList.append(ns.name)
                    ns.state = "match"
                    ns.partner = espName
                else:
                    freeNSList = []
                    newNSPrefer = (bid/esp.NSInfo[ns.name]["weight needs"])
                    for NSName in esp.acceptList:
                        prefer = (esp.NSInfo[NSName]["bid"] /
                                  esp.NSInfo[NSName]["weight needs"])
                        if prefer <= newNSPrefer:
                            freeNSList.append((prefer, NSName))


                    freeNSList.sort()
                    restoreNSList = []
                    denyNSList = []
                    accept = False
                    for value, freeName in freeNSList:
                        esp.acceptList.remove(freeName)
                        restoreNSList.append((value, freeName))
                        # delete NS and VNF from server's serveList and serveNSList

                        for serverName, server in esp.serverList.items():
                            if freeName in server.serveNSList:
                                server.delete(freeName)

                        nsList2 = []
                        nsList2.append(ns.name)
                        for NSName in esp.acceptList:
                            nsList2.append(NSName)
                        preResult, allocation = esp.BO(nsList2, ns.name)
                        if preResult:
                            esp.acceptList.append(ns.name)
                            accept = True
                            break

                    if len(restoreNSList) != 0:
                        # print("ESP", self.name, "try to restore", restoreNSList)
                        restoreNSList.sort()
                        restoreNSList.reverse()
                        for value, NSName in restoreNSList:
                            nsList3 = []
                            nsList3.append(NSName)
                            for oldNS in esp.acceptList:
                                nsList3.append(oldNS)
                            preResult, allocation = esp.BO(nsList3, NSName)
                            if preResult:
                                esp.acceptList.append(NSName)
                                continue
                            else:
                                denyNSList.append(NSName)

                    if accept:
                        if len(denyNSList) != 0:
                            for nsName in denyNSList:
                                for otherNS in NSList:
                                    if nsName == otherNS.name:
                                        otherNS.state = "unmatch"
                                        otherNS.partner = None
                                        otherNS.bids[espName] += 20
                        ns.state = "match"
                        ns.partner = espName
                    else:
                        ns.bids[espName] += 20
        if end is True:
            break
    return total


def readData(data, locationData):
    NSList = []
    ESPList = []
    nOfNS = 0
    for ns in data['NSList']:
        NSList.append(NS.NS(nOfNS, ns['value'], ns['latency'], ns['vnfInfo']))
        nOfNS += 1
    nOfESP = 0
    for esp in data['ESPList']:
        ESPList.append(ESP.ESP(nOfESP, esp, locationData[str(nOfESP)]))
        nOfESP += 1

    return NSList, ESPList


def getLocation():
    with open("dataGenerater/topology_l5.json") as f:
        locationData = json.load(fp=f)
        return locationData["xyAxis"]


def Main():
    # 1:DA-DA  2:DA-Bo  3:DA-CHA  4:DA-RA
    # 5:CHA-DA 6:CHA-Bo 7:CHA-CHA 8:CHA-RA
    # 9:RA-DA  10:RA-Bo 11:RA-CHA 12:RA-RA
    args = argParse()
    if int(args.s) in [1,2,3,4]:
        DF = pd.DataFrame(columns=["ns_utility","ns_profit","ns_latency","ns_true_latency","esp_utility", "matched","iteration"])
    else:
        DF = pd.DataFrame(columns=["ns_utility","ns_profit","ns_latency","ns_true_latency","esp_utility", "matched"])
    locationData = getLocation()

    filename = "N"+str(args.N)+"n"+str(args.n)+"m"+str(args.m)
    with open("dataGenerater/"+filename+".json", "r") as f:
        data = json.load(fp=f)
        totalNOfData = len(data)
        for nOfData, _ in data.items():
            print("(%d/%d)" %(int(nOfData)+1, totalNOfData))
            NSList, ESPList = readData(data[nOfData], locationData)
            # nOfNS = len(NSList)
            # nOfESP = len(NSList)

            if int(args.s) == 1:
                iteration = revisedDA(NSList, ESPList)
            elif int(args.s) == 2:
                iteration = DA_BO(NSList, ESPList)
            elif int(args.s) == 3:
                iteration = DA_CHA(NSList, ESPList)
            elif int(args.s) == 4:
                iteration = DA_RA(NSList, ESPList)
            elif int(args.s) == 5:
                onesideAlgo(NSList, ESPList)
            elif int(args.s) == 6:
                CHA_BO(NSList, ESPList)
            elif int(args.s) == 7:
                CHA_CHA(NSList, ESPList)
            elif int(args.s) == 8:
                CHA_RA(NSList, ESPList)
            elif int(args.s) == 9:
                randomDA(NSList, ESPList)
            elif int(args.s) == 10:
                RA_BO(NSList, ESPList)
            elif int(args.s) == 11:
                RA_CHA(NSList, ESPList)
            elif int(args.s) == 12:
                randomAlgo(NSList, ESPList)
            else:
                print("no such strategy")
                quit()

            # Record
            row = []
            espU = []
            nsU = []
            nsP = []
            nsL = []
            nsTL = []
            matchPair = 0

            for esp in ESPList:
                if int(args.s) == 1:
                    esp.calUtility()
                elif int(args.s) == 2:
                    esp.calUtility()
                elif int(args.s) == 3:
                    esp.calUtility()
                elif int(args.s) == 4:
                    esp.calUtility()
                elif int(args.s) == 5:
                    esp.calUtility()
                elif int(args.s) == 6:
                    esp.calUtility()
                elif int(args.s) == 7:
                    esp.calUtility()
                elif int(args.s) == 8:
                    esp.calUtility()
                elif int(args.s) == 9:
                    esp.calUtility()
                elif int(args.s) == 10:
                    esp.calUtility()
                elif int(args.s) == 11:
                    esp.calUtility()
                elif int(args.s) == 12:
                    esp.calUtilityRandom()
                assert float(esp.utility) >= 0
                espU.append(str(float(esp.utility)))
            for ns in NSList:
                ns.calUtility()
                nsU.append(str(float(ns.utility)))
                nsP.append(str(float(ns.profit)))
                assert float(ns.utility) >= 0
                assert float(ns.profit) >= 0

                if ns.partner is not None:
                    matchPair += 1
                    nsL.append(str(ns.expectedLatency[ns.partner]))
                    if ns.latency is not None:
                        assert ns.expectedLatency[ns.partner] <= ns.latency
                        nsTL.append(str(ns.expectedLatency[ns.partner]))
                    else:
                        nsTL.append(str(0))
            row.append(",".join(nsU))
            row.append(",".join(nsP))
            row.append(",".join(nsL))
            row.append(",".join(nsTL))
            row.append(",".join(espU))
            row.append(str(matchPair))
            if int(args.s) in [1,2,3,4]:
                row.append(str(iteration))
            DF.loc[nOfData] = row

            for i in range(len(NSList)-1, -1, -1):
                del NSList[i]
            for i in range(len(ESPList)-1, -1, -1):
                del ESPList[i]
            del NSList
            del ESPList
            del nsU
            del espU
            del row
            gc.collect()
    if int(args.s) == 1:
        filename = filename + "_DA_DA"
    elif int(args.s) == 2:
        filename = filename + "_DA_BO"
    elif int(args.s) == 3:
        filename = filename + "_DA_CHA"
    elif int(args.s) == 4:
        filename = filename + "_DA_RA"
    elif int(args.s) == 5:
        filename = filename + "_CHA_DA"
    elif int(args.s) == 6:
        filename = filename + "_CHA_BO"
    elif int(args.s) == 7:
        filename = filename + "_CHA_CHA"
    elif int(args.s) == 8:
        filename = filename + "_CHA_RA"
    elif int(args.s) == 9:
        filename = filename + "_RA_DA"
    elif int(args.s) == 10:
        filename = filename + "_RA_BO"
    elif int(args.s) == 11:
        filename = filename + "_RA_CHA"
    elif int(args.s) == 12:
        filename = filename + "_RA_RA"
    writer = pd.ExcelWriter(filename+'.xlsx', engine='xlsxwriter')
    DF.to_excel(writer, index=False)
    writer.save()


if __name__ == '__main__':
    Main()
