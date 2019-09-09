import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from argparse import ArgumentParser

TERM_LIST = {"1": "esp profit", "2": "ns profit", "3": "match", "4":"ns latency", "5":"true latency", "6":"social"}
Data1 = ["N50n10m5", "N50n20m5", "N50n30m5", "N50n40m5", "N50n50m5","N50n60m5", "N50n70m5","N50n80m5", "N50n90m5", "N50n100m5"]
Data = ["N50n50m5","N50n100m5","N50n150m5","N50n200m5",
        "N50n250m5","N50n300m5","N50n350m5", "N50n400m5",
        "N50n450m5", "N50n500m5"]
top = ["DA","CHA","RA"]
bottom = ["DA","BO","CHA","RA"]

def argParse():
    parser = ArgumentParser()
    parser.add_argument("t", help="top strategy: 1-DA, 2-CHA, 3-RA")
    # parser.add_argument("b", help="bottom strategy: 1-DA, 2-BO, 3-CHA, 4-RA")
    parser.add_argument("i", help="term: 1")
    args = parser.parse_args()
    return args




def calU(data):
    payload = []
    for single in data:
        s = str(single).split(",")
        n = len(s)
        total = 0
        for utility in s:
            total += float(utility)
        payload.append(total / n)
    return sum(payload)/len(payload)

def calL(data, cor):
    payload = []
    for single in data:
        s = single.split(",")
        totalLatency = 0
        match = len(s)
        if cor is True:
            for latency in s:
                totalLatency += int(latency)
        else:
            for latency in s:
                if int(latency) == 0:
                    match -= 1
                totalLatency += int(latency)
        payload.append(totalLatency/match)
    return sum(payload)/len(payload)


def Main():
    args = argParse()
    TERM = TERM_LIST[str(args.i)]
    TOP_LIST = {"1":"DA", "2":"CHA", "3":"RA"}
    BOTTOM_LIST = ["DA", "BO", "CHA", "RA"]

    TOP = TOP_LIST[args.t]
    D = {}

    for BOT in BOTTOM_LIST:
        D[BOT] = dict(zip(("ns utility", "ns profit", "esp profit", "ns latency", "match", "true latency", "social"),([],[],[],[],[],[],[])))

    # my = {"ns utility":[], "ns profit":[], "esp profit":[], "ns latency": [], "match": [], "true latency":[], "social":[]}
    # Random = {"ns utility":[], "ns profit":[], "esp profit":[], "ns latency": [], "match": [], "true latency":[], "social":[]}
    # oneside = {"ns utility":[], "ns profit":[], "esp profit":[], "ns latency": [], "match": [], "true latency":[], "social":[]}
    for BOT in BOTTOM_LIST:
        for filename in Data:
            df = pd.read_excel('../nchange/'+filename+'_'+TOP+'_'+BOT+'.xlsx')
            D[BOT]["social"].append((calU(df["ns_profit"])+calU(df["esp_utility"])))
            D[BOT]["ns utility"].append(calU(df["ns_utility"]))
            D[BOT]["esp profit"].append(calU(df["esp_utility"]))
            D[BOT]["ns profit"].append(calU(df["ns_profit"]))
            D[BOT]["ns latency"].append(calL(df["ns_latency"], False))
            D[BOT]["true latency"].append(calL(df["ns_true_latency"], True))
            D[BOT]["match"].append(float(df["matched"].mean()))

    if TERM == "esp profit":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Numbers of Network Services')
        ax.set_ylabel('Profit')
        x = np.linspace(50, 500, 10)
        # print(new_ticks)
        ax.set_xticks(x)
        # plt.title("The number of served network services", fontweight='bold', fontsize='x-large',verticalalignment ='center')
        if TOP == "DA":
            ax.plot(x, D["DA"][TERM], 'o-', label='BP-DNSES')
        else:
            ax.plot(x, D["DA"][TERM], 'o-', label=TOP+'-'+"DA")
        ax.plot(x, D["BO"][TERM], '*-', label=TOP+'-'+"BO")
        ax.plot(x, D["CHA"][TERM], 'x-', label=TOP+'-'+'CHA')
        ax.plot(x, D["RA"][TERM], label=TOP+'-'+'RA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=4)
        # text = ax.text(-0.2,1.05, "Aribitrary text", transform=ax.transAxes)
        # ax.set_title("Avg. Profit of ESPs", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('esp_profit_'+TOP+'.eps')
        plt.show()
    elif TERM == "match":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Numbers of Network Services')
        ax.set_ylabel('Number of Served Network Services')
        x = np.linspace(50, 500, 10)
        # print(new_ticks)
        ax.set_xticks(x)
        if TOP == "DA":
            ax.plot(x, D["DA"][TERM], 'o-', label='BP-DNSES')
        else:
            ax.plot(x, D["DA"][TERM], 'o-', label=TOP+'-'+"DA")
        ax.plot(x, D["BO"][TERM], '*-', label=TOP+'-'+"BO")
        ax.plot(x, D["CHA"][TERM], 'x-', label=TOP+'-'+'CHA')
        ax.plot(x, D["RA"][TERM], label=TOP+'-'+'RA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=4)
        # ax.set_title("Avg. Number of Served Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('match_'+TOP+'.eps')
        plt.show()
    elif TERM == "ns profit":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Numbers of Network Services')
        ax.set_ylabel('Profit')
        x = np.linspace(50, 500, 10)
        # print(new_ticks)
        ax.set_xticks(x)
        if TOP == "DA":
            ax.plot(x, D["DA"][TERM], 'o-', label='BP-DNSES')
        else:
            ax.plot(x, D["DA"][TERM], 'o-', label=TOP+'-'+"DA")
        ax.plot(x, D["BO"][TERM], '*-', label=TOP+'-'+"BO")
        ax.plot(x, D["CHA"][TERM], 'x-', label=TOP+'-'+'CHA')
        ax.plot(x, D["RA"][TERM], label=TOP+'-'+'RA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=4)
        # ax.set_title("Avg. Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('ns_profit_'+TOP+'.eps')
        plt.show()
    elif TERM == "ns latency":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Numbers of Network Services')
        ax.set_ylabel('Total Profit')
        x = np.linspace(50, 500, 10)
        # print(new_ticks)
        ax.set_xticks(x)
        if TOP == "DA":
            ax.plot(x, D["DA"][TERM], 'o-', label='BP-DNSES')
        else:
            ax.plot(x, D["DA"][TERM], 'o-', label=TOP+'-'+"DA")
        ax.plot(x, D["BO"][TERM], '*-', label=TOP+'-'+"BO")
        ax.plot(x, D["CHA"][TERM], 'x-', label=TOP+'-'+'CHA')
        ax.plot(x, D["RA"][TERM], label=TOP+'-'+'RA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=4)
        # ax.set_title("Avg. Total Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('ns_latency_'+TOP+'.eps')
        plt.show()
    elif TERM == "true latency":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Numbers of Network Services')
        ax.set_ylabel('Profit')
        x = np.linspace(50, 500, 10)
        # print(new_ticks)
        ax.set_xticks(x)
        if TOP == "DA":
            ax.plot(x, D["DA"][TERM], 'o-', label='BP-DNSES')
        else:
            ax.plot(x, D["DA"][TERM], 'o-', label=TOP+'-'+"DA")
        ax.plot(x, D["BO"][TERM], '*-', label=TOP+'-'+"BO")
        ax.plot(x, D["CHA"][TERM], 'x-', label=TOP+'-'+'CHA')
        ax.plot(x, D["RA"][TERM], label=TOP+'-'+'RA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=4)
        # ax.set_title("Avg. Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('true_latency.eps')
        plt.show()
    elif TERM == "social":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Numbers of Network Services')
        ax.set_ylabel('Social Welfare')
        x = np.linspace(50, 500, 10)
        # print(new_ticks)
        ax.set_xticks(x)
        if TOP == "DA":
            ax.plot(x, D["DA"][TERM], 'o-', label='BP-DNSES')
        else:
            ax.plot(x, D["DA"][TERM], 'o-', label=TOP+'-'+"DA")
        ax.plot(x, D["BO"][TERM], '*-', label=TOP+'-'+"BO")
        ax.plot(x, D["CHA"][TERM], 'x-', label=TOP+'-'+'CHA')
        ax.plot(x, D["RA"][TERM], label=TOP+'-'+'RA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=4)
        ax.set_title("Social Welfare", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('social_welfare_final.eps')
        plt.show()




if __name__ == '__main__':
    Main()
