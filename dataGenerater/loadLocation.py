import json
import numpy as np
import copy
import matplotlib.pyplot as plt
import math


plt.gcf().clear()
fig = plt.figure(1)
ax = fig.add_subplot(111)


def Main():
    # numOfVnf
    data = {}

    with open("topology_l5.json", 'r') as f:
        data = json.load(fp=f)
    area = data["area"]
    xyAxis = data["xyAxis"]


    for k, v in area.items():
        x = v["x"]
        y = v["y"]
        for i in range(len(x)):
            x[i] = 100*x[i] - 50
            y[i] = 100*y[i] - 50

        ax.plot(x, y, "g", alpha=0.3)
        ax.fill(x, y, "g", alpha=0.05)



    X = {}
    Y = {}
    for i in range(int(5)):
        x = []
        y = []
        for j in range(5):
            x.append(xyAxis[str(i)][str(j)]["x"])
            y.append(xyAxis[str(i)][str(j)]["y"])
        for j in range(len(x)):
            x[j] = 100*x[j]-50
            y[j] = 100*y[j]-50
        X[str(i)] = copy.deepcopy(x)
        Y[str(i)] = copy.deepcopy(y)

    color = ["red", "blue", "purple", "orange", "cyan"]
    for i in range(int(5)):
        ax.scatter(X[str(i)], Y[str(i)], color=color[i], label = ("ESP"+" "+str(i)))

    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(handles, labels, bbox_to_anchor=(1.02,0.8),loc='center left')
    # text = ax.text(-0.2,1.05, "Aribitrary text", transform=ax.transAxes)
    ax.set_title("The Topology of Edge Servers of ESPs")
    # ax.grid('on')
    plt.xticks(np.arange(-50, 60, step=10))
    ax.set_xlabel('X')
    plt.yticks(np.arange(-50, 60, step=10))
    ax.set_ylabel('Y')
    plt.tight_layout()

    # ax.set_xlabel('X')

    # ax.set_ylabel('Y')
    plt.savefig("123topology_l5.pdf")
    plt.show()


    """
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

    """
    plt.xlim(0, 1)
    plt.xticks(())  # ignore xticks
    plt.ylim(0, 1)
    plt.yticks(())  # ignore yticks
    plt.savefig("location.png")
    """


    """
    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(handles, labels, bbox_to_anchor=(1.02,0.8),loc='center left')
    # text = ax.text(-0.2,1.05, "Aribitrary text", transform=ax.transAxes)
    ax.set_title("Edge server topology")
    # ax.grid('on')
    plt.tight_layout()
    # plt.savefig("topology.png")
    plt.show()
    """




if __name__ == '__main__':
    Main()
