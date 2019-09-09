import random


class NS():

    def __init__(self, number, value, latency, vnfInfo):
        self.name = str(number)
        self.value = value
        self.bids = dict()
        self.state = "unmatch"
        self.partner = None
        self.latency = latency
        self.utility = 0
        self.profit = 0

        self.expectedLatency = dict()
        self.vnfList = {}
        self.potentialESPList = []
        self.totalNeeds = {}

        self.getVnfList(vnfInfo)

        # for random
        self.denyList = []

    def getVnfList(self, info):
        n = 0
        for vnf in info:
            self.vnfList[str(n)] = VNF(self.name, str(n), vnf)
            n += 1

    def initialVnfList(self, spec):
        for vnfName, vnf in self.vnfList.items():
            vnf.getNeeds(spec)
        for r, _ in list(spec.values())[0].items():
            self.totalNeeds[r] = 0
        self.getTotalNeeds()

    def getTotalNeeds(self):
        for vnfName, vnf in self.vnfList.items():
            for r, q in vnf.needs.items():
                self.totalNeeds[r] += q

    def query(self, esp):
        # query whether ESP has enough resouce to serve
        # and the expected latency
        name, price, expectedLatency = esp.calReservationPriceAndDelay(self)
        if (price is not None) and (price <= self.value):
            if self.latency is None:
                self.bids[name] = price
                self.potentialESPList.append(name)
                self.expectedLatency[name] = expectedLatency
            else:
                if expectedLatency is not None:
                    self.bids[name] = price
                    self.potentialESPList.append(name)
                    self.expectedLatency[name] = expectedLatency

    def ProposeESPAndBid(self):
        esp = self.calPreference()
        if esp is None:
            return None, None
        else:
            return esp, self.bids[esp]

    def calPreference(self):
        maxU = 0
        proposeList = []
        deleteList = []
        for esp, bid in self.bids.items():
            if self.latency is None:
                U = (self.value - bid)
            else:
                if self.expectedLatency[esp] is None:
                    U = -1
                else:
                    U = (self.value - bid)/self.expectedLatency[esp]
            if U > maxU:
                maxU = U
                proposeList = []
                proposeList.append(esp)
            elif U < maxU and U >= 0:
                continue
            elif U == maxU:
                proposeList.append(esp)
            elif U < 0:
                deleteList.append(esp)
        if len(deleteList) != 0:
            for esp in deleteList:
                del self.bids[esp]
        if len(proposeList) == 0:
            self.state = "match"
            self.partner = None
            return None
        return random.choice(proposeList)

    def calUtility(self):
        if self.partner is None:
            self.profit = 0
            self.utility = 0
        else:
            self.profit = self.value - self.bids[self.partner]
            self.utility = (self.value - self.bids[self.partner])/self.expectedLatency[self.partner]
            assert self.profit >= 0
            assert self.utility >= 0

class VNF():
    def __init__(self, owner, name, vnfInfo):
        self.owner = owner
        self.name = name
        self.type = vnfInfo["type"]
        self.location = vnfInfo["location"]
        self.needs = {}
        self.preferenceList = []
        self.allocatedServerRandom = None

    def getNeeds(self, spec):
        for key, value in spec[self.type].items():
            self.needs[key] = value
