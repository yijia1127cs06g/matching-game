import copy
import numpy as np
import random
import math


class ESP():

    def __init__(self, number, serverInfo, SL):
        self.name = str(number)
        self.utility = 0
        self.resourceFactors = {"cpu": 0.5, "storage": 0.2, "memory": 0.3}
        self.serverList = {}  # record each server
        self.acceptList = []  # record the accepted NS
        self.NSInfo = {}
        self.totalResources = {"cpu": 0, "memory": 0, "storage": 0}
        self.getServerList(serverInfo, SL)
        total = 0
        for r, q in self.totalResources.items():
            total += (1/q)
        for r, q in self.totalResources.items():
            self.resourceFactors[r] = (1/q)/total

    def check(self):
        if len(self.acceptList) != len(set(self.acceptList)):
            print("Redundant")
            print(self.acceptList)

    def getServerList(self, info, SL):
        n = 0
        for server in info:
            for r, q in server["resources"].items():
                self.totalResources[r] += q
            self.serverList[str(n)] = Server(
                self.name, str(n), server, SL[str(n)])
            n += 1

    def calReservationPriceAndDelay(self, ns):
        name = ns.name
        totalPrice = 0
        serveLocation = dict()
        # Calculate the cost for each vnf in ns
        for vnfName, vnf in ns.vnfList.items():
            price, location = self.calVnfCostAndLocation(vnf)
            if price is not None:
                totalPrice += price
                serveLocation[vnfName] = location
            else:
                return self.name, None, None

        # calculate latency
        rawDistance = 0
        processingTime = 0
        for i in range(len(ns.vnfList)):
            VMType = ns.vnfList[str(i)].type
            if VMType == "MEDIUM":
                processingTime += 1
            elif VMType == "LARGE":
                processingTime += 2
            elif VMType == "XLARGE":
                processingTime += 4
            elif VMType == "XXLARGE":
                processingTime += 8
            if i == (len(ns.vnfList)-1):
                continue
            if serveLocation[str(i)] == serveLocation[str(i+1)]:
                continue
            else:
                pointX = (self.serverList[serveLocation[str(
                    i)]].geo["x"], self.serverList[serveLocation[str(i)]].geo["y"])
                pointY = (self.serverList[serveLocation[str(
                    i+1)]].geo["x"], self.serverList[serveLocation[str(i+1)]].geo["y"])
                rawDistance += math.sqrt((pointX[0]-pointY[0])
                                         ** 2+(pointX[1]-pointY[1])**2)

        expectedLatency = int(rawDistance*4) + processingTime
        # Record the information of NS
        info = {}
        if ns.latency is not None and ns.latency < expectedLatency:
            expectedLatency = None

        info["expected latency"] = expectedLatency
        info["total needs"] = ns.totalNeeds
        info["weight needs"] = sum(
            self.resourceFactors[r] * q for r, q in ns.totalNeeds.items())
        info["total cost"] = 0
        info["vnf list"] = ns.vnfList
        info["location list"] = None
        info["bid"] = None
        info["latency"] = ns.latency

        self.NSInfo[name] = copy.deepcopy(info)
        del info
        return self.name, totalPrice, expectedLatency

    def calVnfCostAndLocation(self, vnf):
        # return the min cost and location of present server state
        isSatisfy = False
        minPrice = float('inf')
        allocateLocation = None
        for loc in vnf.location:
            for serverName, server in self.serverList.items():
                if server.location == loc:
                    if server.chkCapacity(vnf.needs):
                        isSatisfy = True
                        price = server.calCost(vnf.needs)
                        if price < minPrice:
                            minPrice = price
                            allocateLocation = serverName
        if isSatisfy:
            return minPrice, allocateLocation
        else:
            return None, allocateLocation

    def acceptOrDenyTemp(self, newNSName, bid):
        self.NSInfo[newNSName]["bid"] = bid
        nsList = []
        nsList.append(newNSName)
        for NSName in self.acceptList:
            nsList.append(NSName)
        # print("New comer: NS", newNSName)
        # print("ESP", self.name, "has already accept", self.acceptList)
        # print("PARTICANPT", nsList)
        result, allocation = self.AllocateDAAlgo(nsList, newNSName)

        if result is False:
            return False
        else:
            self.acceptList.append(newNSName)
            return True
            # can allocate, calculate cost
            """
            for NSName, vnfList in allocation.items():
                totalCost = 0
                for vnfName, serverName in vnfList.items():
                    cost = self.serverList[serverName].calCost(
                        self.NSInfo[NSName]["vnf list"][vnfName].needs)
                    totalCost += cost
                if totalCost > self.NSInfo[NSName]["bid"]:
                    return False

            self.acceptList.append(newNSName)

        # mark vnf on server

        for vnfName, serverName in allocation[newNSName].items():
            self.serverList[serverName].mark(
                self.NSInfo[newNSName]["vnf list"][vnfName])

        return True
            """

    def tryReallocate(self, newNSName, bid):
        freeNSList = []
        newNSPrefer = (bid/self.NSInfo[newNSName]["weight needs"])
        # print("Before Reallocating, ESP has accepted", self.acceptList)
        for NSName in self.acceptList:
            prefer = (self.NSInfo[NSName]["bid"] /
                      self.NSInfo[NSName]["weight needs"])
            if prefer <= newNSPrefer:
                freeNSList.append((prefer, NSName))

        if len(freeNSList) == 0:
            # print("No NS'preference is smaller than NS", newNSName)
            return False, None

        # print("NS", newNSName, "'s preference can beat", freeNSList)

        freeNSList.sort()
        restoreNSList = []
        denyNSList = []
        accept = False
        for value, freeName in freeNSList:
            self.acceptList.remove(freeName)
            restoreNSList.append((value, freeName))
            # delete NS and VNF from server's serveList and serveNSList

            for serverName, server in self.serverList.items():
                if freeName in server.serveNSList:
                    server.delete(freeName)

            if self.acceptOrDenyTemp(newNSName, bid):
                # print("reallocated success")
                accept = True
                break

        if len(restoreNSList) != 0:
            # print("ESP", self.name, "try to restore", restoreNSList)
            restoreNSList.sort()
            restoreNSList.reverse()
            for value, NSName in restoreNSList:
                if self.acceptOrDenyTemp(NSName, self.NSInfo[NSName]["bid"]):
                    # continue
                    # self.acceptList.append(NSName)
                    continue
                else:
                    denyNSList.append(NSName)

        if accept:
            return True, denyNSList
        else:
            return False, denyNSList

    def AllocateDAAlgo(self, NSPlayers, newNSName):
        # two-side matching
        # player1 : vnfs {"no":{"vnf":vnf(object), "state": "unmatch",
        #                       "preference list":[], "parnter":None }}
        vnfPlayers = self.initVnfPlayers(NSPlayers)
        # player2 : servers
        self.initServerPlayers()

        # print("Before AllocateDAAlgo")
        # for serverName, server in self.serverList.items():
        # print("Server", server.name, "now has", server.allocateResources)
        # print("Server", server.name, "has already serves", server.serveNSList)
        #     for vnf in server.serveVnfList:
        # print("I belong to", vnf.owner, ", I'm number ", vnf.name, "I need", vnf.needs)

        while True:
            end = True
            for vnfNo, vnf in vnfPlayers.items():
                if vnf["state"] == "match":
                    continue
                if len(vnf["preference list"]) != 0:
                    end = False
                    proposeServer = vnf["preference list"].pop()[1]
                    server = self.serverList[proposeServer]
                    if server.chkCapacity(vnf["vnf"].needs):
                        # print("vnf", vnf["vnf"].name, "can be allocated at server", proposeServer)
                        server.allocateVnf(
                            vnf["vnf"].needs, (vnf["vnf"].owner, vnf["vnf"].name))
                        vnf["state"] = "match"
                        vnf["parnter"] = proposeServer
                    else:
                        freeList = []
                        newPrefer = self.NSInfo[vnf["vnf"].owner]["bid"]/sum(
                            server.resourceFactors[r] * q for r, q in vnf["vnf"].needs.items())
                        for no in server.allocateList:
                            prefer = self.NSInfo[no[0]]["bid"]/sum(
                                server.resourceFactors[r] * q for r, q in self.NSInfo[no[0]]["vnf list"][no[1]].needs.items())
                            if newPrefer > prefer:
                                freeList.append((prefer, no))
                        if len(freeList) == 0:
                            continue
                        else:
                            restore = True
                            freeList.sort()
                            for freeVnfNo in freeList:
                                server.freeVnf(vnfPlayers[str(freeVnfNo[1])]["vnf"].needs,
                                               (vnfPlayers[str(freeVnfNo[1])]["vnf"].owner, vnfPlayers[str(freeVnfNo[1])]["vnf"].name))
                                vnfPlayers[str(freeVnfNo[1])
                                           ]["state"] = "unmatch"
                                vnfPlayers[str(freeVnfNo[1])]["parnter"] = None
                                if server.chkCapacity(vnf["vnf"].needs):
                                    server.allocateVnf(
                                        vnf["vnf"].needs,
                                        (vnf["vnf"].owner, vnf["vnf"].name)
                                        )
                                    vnf["state"] = "match"
                                    vnf["parnter"] = proposeServer
                                    restore = False
                                    break
                            if restore:
                                # still no resource after delete all vnf
                                # behind new vnf
                                for restoreVnfNo in freeList:
                                    server.allocateVnf(vnfPlayers[str(restoreVnfNo[1])]["vnf"].needs,
                                                       (vnfPlayers[str(restoreVnfNo[1])]["vnf"].owner, vnfPlayers[str(restoreVnfNo[1])]["vnf"].name))
                                    vnfPlayers[str(freeVnfNo[1])
                                               ]["state"] = "match"
                                    vnfPlayers[str(freeVnfNo[1])
                                               ]["parnter"] = proposeServer
            if end is True:
                break
        # check all vnf is satisfy
        allocation = {}
        for vnfNo, vnf in vnfPlayers.items():
            if vnf["state"] == "unmatch":
                return False, allocation
        # print("All VNF can be served")
        # all vnf is satisfy
        """
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner in allocation:
                allocation[VNF.owner][VNF.name] = vnf["parnter"]
            else:
                allocation[VNF.owner] = dict(
                    zip(VNF.name, vnf["parnter"]))
        """
        ###
        TOTAL_COST = {}
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner not in TOTAL_COST:
                TOTAL_COST[VNF.owner] = 0
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)
            else:
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)
        # print(TOTAL_COST)
        for ns, COST in TOTAL_COST.items():
            # print("NS's Cost =", COST, "NS's bid =",self.NSInfo[ns]["bid"])
            if COST > self.NSInfo[ns]["bid"]:
                return False, allocation
        # print("All cost is smaller than NS's price")

        for serverName, server in self.serverList.items():
            server.initForMark()
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner == newNSName:
                SERVER = self.serverList[vnf["parnter"]]
                SERVER.mark(VNF)
        # print("After AllocateDAAlgo")
        # for serverName, server in self.serverList.items():
            # print("Server", server.name, "has already serves", server.serveNSList)
            # for vnf in server.serveVnfList:
                # print("I belong to", vnf.owner, ", I'm number ", vnf.name)

        return True, allocation

    def initVnfPlayers(self, NSPlayers):
        n = 0
        temp = {}
        for NSPlayer in NSPlayers:
            for no, vnf in self.NSInfo[NSPlayer]["vnf list"].items():
                preferencelist = self.calVnfPreferenceList(vnf)
                temp[str((vnf.owner, vnf.name))] = dict(
                    zip(("vnf", "state", "preference list", "parnter"),
                        (vnf, "unmatch", preferencelist, None)))
                n += 1

        return temp

    def initServerPlayers(self):
        for name, server in self.serverList.items():
            server.initForAllocate()

    def calVnfPreferenceList(self, vnf):
        preferenceList = []
        for name, server in self.serverList.items():
            if server.location in vnf.location:
                price = server.calCost(vnf.needs)
                preferenceList.append((price, name))
        preferenceList.sort()
        preferenceList.reverse()
        return preferenceList

    def calVnfCostAndSatify(self, vnf):
        # return random the cost and location of present server state
        isSatisfy = False
        allocateLocation = None
        for loc in vnf.location:
            for serverName, server in self.serverList.items():
                if server.location == loc:
                    if server.chkRemainCapacity(vnf.needs):
                        isSatisfy = True
                        price = server.calCost(vnf.needs)
                        allocateLocation = server.name
                if isSatisfy:
                    break
        if isSatisfy:
            return price, allocateLocation
        else:
            return None, allocateLocation

    def calUtility(self):
        self.utility = 0
        for serverName, server in self.serverList.items():
            for vnf in server.serveVnfList:
                self.NSInfo[vnf.owner]["total cost"] += server.calCost(
                    vnf.needs)
        for NSName in self.acceptList:
            self.utility += (self.NSInfo[NSName]["bid"] -
                             self.NSInfo[NSName]["total cost"])

    def calUtilityRandom(self):
        self.utility = 0
        for NSName in self.acceptList:
            self.utility += (self.NSInfo[NSName]["bid"] -
                             self.NSInfo[NSName]["total cost"])

    def randomAllocation(self, nsList, newNSName):
        # player1 : vnfs {"no":{"vnf":vnf(object), "state": "unmatch",
        #                       "preference list":[], "parnter":None }}
        vnfPlayers = self.initVnfPlayers(nsList)
        self.initServerPlayers()
        # player2 : servers
        vnfNoList = []
        for no, vnf in vnfPlayers.items():
            vnfNoList.append(no)

        while len(vnfNoList) != 0:
            vnfNo = random.choice(vnfNoList)
            vnfNoList.remove(vnfNo)
            vnf = vnfPlayers[vnfNo]
            isAllocated = False
            while len(vnf["preference list"]) != 0:
                if vnf["state"] == "match":
                    break
                proposePriceServer = random.choice(vnf["preference list"])
                vnf["preference list"].remove(proposePriceServer)
                proposeServer = proposePriceServer[1]
                server = self.serverList[proposeServer]
                if server.chkCapacity(vnf["vnf"].needs):
                    server.allocateVnf(
                        vnf["vnf"].needs, (vnf["vnf"].owner, vnf["vnf"].name))
                    vnf["state"] = "match"
                    vnf["parnter"] = proposeServer
                    isAllocated = True
            if isAllocated is False:
                return False, {}

        assert len(vnfNoList) == 0

        allocation = {}
        for vnfNo, vnf in vnfPlayers.items():
            if vnf["state"] == "unmatch":
                return False, allocation
        # print("All VNF can be served")
        # all vnf is satisfy
        """
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner in allocation:
                allocation[VNF.owner][VNF.name] = vnf["parnter"]
            else:
                allocation[VNF.owner] = dict(
                    zip(VNF.name, vnf["parnter"]))
        """
        ###
        TOTAL_COST = {}
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner not in TOTAL_COST:
                TOTAL_COST[VNF.owner] = 0
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)
            else:
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)
        # print(TOTAL_COST)
        for ns, COST in TOTAL_COST.items():
            # print("NS's Cost =", COST, "NS's bid =",self.NSInfo[ns]["bid"])
            if COST > self.NSInfo[ns]["bid"]:
                return False, allocation
        # print("All cost is smaller than NS's price")

        for serverName, server in self.serverList.items():
            server.initForMark()
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner == newNSName:
                SERVER = self.serverList[vnf["parnter"]]
                SERVER.mark(VNF)
        # print("After AllocateDAAlgo")
        # for serverName, server in self.serverList.items():
            # print("Server", server.name, "has already serves", server.serveNSList)
            # for vnf in server.serveVnfList:
                # print("I belong to", vnf.owner, ", I'm number ", vnf.name)

        return True, allocation

    def CHA(self, NSPlayers, newNSName):
        vnfPlayers = self.initVnfPlayers(NSPlayers)
        self.initServerPlayers()
        vnfNoList = []
        for no, vnf in vnfPlayers.items():
            vnfNoList.append(no)

        while len(vnfNoList) != 0:
            vnfNo = random.choice(vnfNoList)
            vnfNoList.remove(vnfNo)
            vnf = vnfPlayers[vnfNo]
            while len(vnf["preference list"]) != 0:
                proposeServer = vnf["preference list"].pop()[1]
                server = self.serverList[proposeServer]
                if server.chkCapacity(vnf["vnf"].needs):
                    server.allocateVnf(
                        vnf["vnf"].needs, (vnf["vnf"].owner, vnf["vnf"].name))
                    vnf["state"] = "match"
                    vnf["parnter"] = proposeServer
                    break

        allocation = {}
        for vnfNo, vnf in vnfPlayers.items():
            if vnf["state"] == "unmatch":
                return False, allocation

        TOTAL_COST = {}
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner not in TOTAL_COST:
                TOTAL_COST[VNF.owner] = 0
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)
            else:
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)

        for ns, COST in TOTAL_COST.items():
            if COST > self.NSInfo[ns]["bid"]:
                return False, allocation

        for serverName, server in self.serverList.items():
            server.initForMark()
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner == newNSName:
                SERVER = self.serverList[vnf["parnter"]]
                SERVER.mark(VNF)
        return True, allocation

    def BO(self, NSPlayers, newNSName):
        vnfPlayers = self.initVnfPlayers(NSPlayers)
        self.initServerPlayers()
        serverPlayersReceiveList = {}

        while True:
            end = True
            for serverName, _ in self.serverList.items():
                serverPlayersReceiveList[serverName] = []
            for vnfNo, vnf in vnfPlayers.items():
                if vnf["state"] == "unmatch":
                    if len(vnf["preference list"]) == 0:
                        return False, {}
                    end = False
                    proposeServer = vnf["preference list"].pop()[1]
                    serverPlayersReceiveList[proposeServer].append(vnfNo)

            for serverNo, receiveList in serverPlayersReceiveList.items():
                aList = []
                server = self.serverList[serverNo]
                for vnfNo in receiveList:
                    vnf = vnfPlayers[vnfNo]
                    prefer = self.NSInfo[vnf["vnf"].owner]["bid"]/sum(
                        server.resourceFactors[r] * q for r, q in vnf["vnf"].needs.items())
                    aList.append((prefer, vnfNo))
                aList.sort()
                aList.reverse()
                for (prefer, vnfNo) in aList:
                    vnf = vnfPlayers[vnfNo]
                    if server.chkCapacity(vnf["vnf"].needs):
                        # print("vnf", vnf["vnf"].name, "can be allocated at server", proposeServer)
                        server.allocateVnf(
                            vnf["vnf"].needs, (vnf["vnf"].owner, vnf["vnf"].name))
                        vnf["state"] = "match"
                        vnf["parnter"] = serverNo
            if end is True:
                break

        allocation = {}
        for vnfNo, vnf in vnfPlayers.items():
            if vnf["state"] == "unmatch":
                return False, allocation

        TOTAL_COST = {}
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner not in TOTAL_COST:
                TOTAL_COST[VNF.owner] = 0
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)
            else:
                TOTAL_COST[VNF.owner] += self.serverList[vnf["parnter"]
                                                         ].calCost(VNF.needs)

        for ns, COST in TOTAL_COST.items():
            if COST > self.NSInfo[ns]["bid"]:
                return False, allocation

        for serverName, server in self.serverList.items():
            server.initForMark()
        for vnfNo, vnf in vnfPlayers.items():
            VNF = vnf["vnf"]
            if VNF.owner == newNSName:
                SERVER = self.serverList[vnf["parnter"]]
                SERVER.mark(VNF)
        return True, allocation


class Server():
    def __init__(self, owner, name, info, geoSL):
        self.owner = owner
        self.name = name
        self.location = info["location"]

        self.totalResources = info["resources"]
        self.remainResources = copy.deepcopy(self.totalResources)
        self.cost = info["cost"]
        self.allocateList = []
        # For final allocation
        self.serveVnfList = []
        # === Optional ===
        # self.serveList = set()
        self.serveNSList = set()

        # For allocation resource in real
        self.allocateResources = copy.deepcopy(self.totalResources)
        self.resourceFactors = {"cpu": 0, "memory": 0, "storage": 0}
        totalFactor = 0
        for r, q in self.totalResources.items():
            totalFactor += (1/q)
        for r, q in self.totalResources.items():
            self.resourceFactors[r] = (1/q)/totalFactor

        self.geo = {"x": 0, "y": 0}  # for calculate latency
        for axis, point in geoSL.items():
            self.geo[axis] = point

    def chkCapacity(self, needs):
        for r, q in needs.items():
            if self.remainResources[r] < q:
                return False
        return True

    def initForAllocate(self):
        # fill resource
        for r, q in self.totalResources.items():
            self.remainResources[r] = q
        # print("server", self.name, "has", self.totalResources)
        # print("server", self.name, "has", self.remainResources)
        # clean allocate list
        self.allocateList = []

    def calCost(self, needs):
        price = 0
        for r, q in needs.items():
            price += (self.cost[r] * q)
        return price

    def allocateVnf(self, needs, vnfOwnerName):
        # print("\t\tBefore allocated: ESP "+self.owner+"'s server",
        #       self.name, "remain:", self.remainResources)
        # print("\t\tneeds:", needs)
        for r, q in needs.items():
            self.remainResources[r] -= q
            assert self.remainResources[r] >= 0
        # print("\t\tAfter allocated: ESP "+self.owner+"'s server",
        #       self.name, "remain:", self.remainResources)
        # print("\t\tneeds:", needs)
        # self.allocateList.append(vnfOwnerName)

    def freeVnf(self, needs, vnfOwnerName):
        for r, q in needs.items():
            self.remainResources[r] += q
        for i in range(len(self.allocateList)):
            if self.allocateList[i][0] == vnfOwnerName[0] and self.allocateList[i][1] == vnfOwnerName[1]:
                deleteIdx = i
                break
        else:
            assert False
        self.allocateList.pop(deleteIdx)

    def initForMark(self):
        for r, q in self.totalResources.items():
            self.allocateResources[r] = q
        self.serveVnfList = []
        self.serveNSList = set()

    def mark(self, vnf):
        for abc in self.serveVnfList:
            assert abc is not vnf.name
        self.serveVnfList.append(vnf)
        # === Optional use ===
        self.serveNSList.add(vnf.owner)
        # self.serveList.add((vnf.owner, vnf.name))

        # print("\t\tBefore make: ESP "+self.owner+"'s server",
        #       self.name, "remain:", self.allocateResources)
        # print("\t\tNS", vnf.owner+"'s vnf", vnf.name, "needs:", vnf.needs)
        for r, q in vnf.needs.items():
            self.allocateResources[r] -= q
            assert self.allocateResources[r] >= 0
        # print("\t\tAfter make: ESP "+self.owner+"'s server",
        #       self.name, "remain:", self.allocateResources)

    def delete(self, NSName):
        """
        Optional
        temp = list(self.serveList)
        for pair in temp:
            if pair[0] == NSName:
                self.serveList.remove(pair)
        """
        deleteIdx = []
        temp = self.serveVnfList.copy()
        for i in range(len(temp)):
            if temp[i].owner == NSName:
                deleteIdx.append(i)
        deleteIdx.sort()
        deleteIdx.reverse()
        for i in deleteIdx:
            for r, q in self.serveVnfList[i].needs.items():
                self.allocateResources[r] += q
            self.serveVnfList.pop(i)
        # self.serveNSList.remove(NSName)
        """
        for i in range(len(temp)):
            if temp[i].owner == NSName:
                print("\t\tBefore delete: ESP "+self.owner+"'s server",
                      self.name, "remain:", self.allocateResources)
                print("\t\tNS", temp[i].owner+"'s vnf",
                      temp[i].name, "needs:", temp[i].needs)
                for r, q in temp[i].needs.items():
                    self.allocateResources[r] += q
                print("\t\tAfter delete: ESP "+self.owner+"'s server",
                      self.name, "remain:", self.allocateResources)
                for vnf in self.serveVnfList:
                    if vnf.owner == temp[i].owner and vnf.name == temp[i].name:
                        self.serveVnfList.remove(vnf)
                        break
        self.serveNSList.remove(NSName)

        for vnf in temp:
            if vnf.owner == NSName:
                print("\t\tBefore delete: ESP "+self.owner+"'s server",
                      self.name, "remain:", self.allocateResources)
                print("\t\tNS", vnf.owner+"'s vnf",
                      vnf.name, "needs:", vnf.needs)
                for r, q in vnf.needs.items():
                    self.allocateResources[r] += q
                print("\t\tAfter delete: ESP "+self.owner+"'s server",
                      self.name, "remain:", self.allocateResources)
                print(self.serveVnfList[0] is vnf)
                print(self.serveVnfList[0].owner, self.serveVnfList[0].owner)
                print(vnf.owner)
                self.serveVnfList.remove(vnf)
        self.serveNSList.remove(NSName)
        """

    def demark(self, vnf):
        deleteIdx = []
        temp = self.serveVnfList.copy()
        for i in range(len(temp)):
            if temp[i].owner == NSName:
                deleteIdx.append(i)
        deleteIdx.sort()
        deleteIdx.reverse()
        for i in deleteIdx:
            for r, q in self.serveVnfList[i].needs.items():
                self.allocateResources[r] += q
            self.serveVnfList.pop(i)
        self.serveNSList.remove(NSName)

    def chkRemainCapacity(self, needs):
        for r, q in needs.items():
            if self.allocateResources[r] < q:
                return False
        return True

    def finalAllocation(self):
        # === For Justify anser ===
        # ===     Don't use     ===
        self.allocatetemp = copy.deepcopy(self.totalResources)
        for vnf in self.serveVnfList:
            for r, q in vnf.needs.items():
                self.allocatetemp[r] -= q
                assert self.allocatetemp[r] >= 0
