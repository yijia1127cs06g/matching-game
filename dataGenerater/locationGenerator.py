import random
from argparse import ArgumentParser
import numpy as np
import copy
import json
import matplotlib.pyplot as plt
import math


NUM_OF_LOCATION = 5
RADIUS = 0.15
OVERLAP = RADIUS*2+0.02

# plot
plt.gcf().clear()
fig = plt.figure(1)
ax = fig.add_subplot(111)



# fig.savefig('samplefigure', bbox_extra_artists=(lgd,text), bbox_inches='tight')



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


def calDistance(a, b):
    return math.sqrt((float(a[0])-float(b[0]))**2 + (float(a[1])-float(b[1]))**2)


def generateArea():
    area = {}
    plt.xlim(0.0, 1.0)
    plt.ylim(0.0, 1.0)
    for i in range(NUM_OF_LOCATION):
        while True:
            end = True
            reset = False
            a, b = (random.random(), random.random())
            for loc, locInfo in area.items():
                if calDistance(locInfo["center"], (a, b)) < OVERLAP:
                    reset = True
                    break
            if reset is True:
                continue

            theta = np.arange(0, 2*np.pi, 0.01)
            x = list(a + RADIUS * np.cos(theta))
            y = list(b + RADIUS * np.sin(theta))

            for numX, numY in zip(x, y):
                if numX < 0.0 or numX > 1.0:
                    end = False
                    break
                if numY < 0.0 or numY > 1.0:
                    end = False
                    break
            if end is True:
                area[str(i)] = dict(zip(("center", "x", "y"),((str(a),str(b)), x, y)))
                ax.plot(x, y, "g", alpha=0.3)
                ax.fill(x, y, "g", alpha=0.05)
                break
            else:
                continue
    return area


def generateLocation(nOfESP, area):
    xyAxis = {}
    for i in range(nOfESP):
        esp = {}
        for loc, locInfo in area.items():
            centerX = float(locInfo["center"][0])
            centerY = float(locInfo["center"][1])
            while True:
                end = True
                x = np.random.uniform(low = (centerX-RADIUS), high = ((centerX+RADIUS)))
                y = np.random.uniform(low = (centerY-RADIUS), high = ((centerY+RADIUS)))
                if calDistance(locInfo["center"],(x,y)) >= RADIUS:
                    continue
                if end is True:
                    esp[loc] = dict(zip(("x","y"), (x,y)))
                    break

        xyAxis[str(i)] = copy.deepcopy(esp)
    return xyAxis


def Main():
    # numOfVnf
    args = argParse()
    data = {}




    area = generateArea()
    xyAxis = generateLocation(int(args.m), area)
    data["area"] = area
    data["xyAxis"] = xyAxis

    with open("topology123.json", 'w') as f:
        json.dump(data, f, indent=2)



    # Test topology
    X = {}
    Y = {}
    for i in range(int(args.m)):
        x = []
        y = []
        for j in range(NUM_OF_LOCATION):
            x.append(xyAxis[str(i)][str(j)]["x"])
            y.append(xyAxis[str(i)][str(j)]["y"])
        X[str(i)] = copy.deepcopy(x)
        Y[str(i)] = copy.deepcopy(y)

    # T = np.arctan2(Y, X)
    color = ["red", "blue", "purple", "orange", "cyan"]
    for i in range(int(args.m)):
        ax.scatter(X[str(i)], Y[str(i)], color=color[i], label = ("ESP"+" "+str(i)))


    # plt.set_position([0,0,0.8,1])
    # plt.legend(['$sin(x)$'],loc='best',fancybox=True,shadow=True,numpoints=1)
    """
    plt.xlim(0, 1)
    plt.xticks(())  # ignore xticks
    plt.ylim(0, 1)
    plt.yticks(())  # ignore yticks
    plt.savefig("location.png")
    """
    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(handles, labels, bbox_to_anchor=(1.02,0.8),loc='center left')
    # text = ax.text(-0.2,1.05, "Aribitrary text", transform=ax.transAxes)
    ax.set_title("Edge server topology")
    # ax.grid('on')
    plt.tight_layout()
    # plt.savefig("topology.png")
    plt.show()





if __name__ == '__main__':
    Main()
