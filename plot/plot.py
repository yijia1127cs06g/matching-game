import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

TERM = "match"
Data1 = ["N50n10m5", "N50n20m5", "N50n30m5", "N50n40m5", "N50n50m5","N50n60m5", "N50n70m5","N50n80m5", "N50n90m5", "N50n100m5"]
Data = ["N50n50m5","N50n100m5","N50n150m5","N50n200m5",
        "N50n250m5","N50n300m5","N50n350m5", "N50n400m5",
        "N50n450m5", "N50n500m5"]

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
    my = {"ns utility":[], "ns profit":[], "esp profit":[], "ns latency": [], "match": [], "true latency":[], "social":[]}
    Random = {"ns utility":[], "ns profit":[], "esp profit":[], "ns latency": [], "match": [], "true latency":[], "social":[]}
    oneside = {"ns utility":[], "ns profit":[], "esp profit":[], "ns latency": [], "match": [], "true latency":[], "social":[]}
    for filename in Data:
        df = pd.read_excel('../nchange/'+filename+'_random'+'.xlsx')
        Random["social"].append((calU(df["ns_profit"])+calU(df["esp_utility"])))
        Random["ns utility"].append(calU(df["ns_utility"]))
        Random["esp profit"].append(calU(df["esp_utility"]))
        Random["ns profit"].append(calU(df["ns_profit"]))
        Random["ns latency"].append(calL(df["ns_latency"], False))
        Random["true latency"].append(calL(df["ns_true_latency"], True))
        Random["match"].append(float(df["matched"].mean()))
    for filename in Data:
        df = pd.read_excel('../'+filename+'_my'+'.xlsx')
        my["social"].append((calU(df["ns_profit"])+calU(df["esp_utility"])))
        my["ns utility"].append(calU(df["ns_utility"]))
        my["esp profit"].append(calU(df["esp_utility"]))
        my["ns profit"].append(calU(df["ns_profit"]))
        my["ns latency"].append(calL(df["ns_latency"], False))
        my["true latency"].append(calL(df["ns_true_latency"], True))
        my["match"].append(float(df["matched"].mean()))

    for filename in Data:
        df = pd.read_excel('../'+filename+'_oneside'+'.xlsx')
        oneside["social"].append((calU(df["ns_profit"])+calU(df["esp_utility"])))
        oneside["ns utility"].append(calU(df["ns_utility"]))
        oneside["esp profit"].append(calU(df["esp_utility"]))
        oneside["ns profit"].append(calU(df["ns_profit"]))
        oneside["ns latency"].append(calL(df["ns_latency"], False))
        oneside["true latency"].append(calL(df["ns_true_latency"], True))
        oneside["match"].append(float(df["matched"].mean()))

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
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        ax.plot(x, Random[TERM], '*-', label='Random')
        ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        # text = ax.text(-0.2,1.05, "Aribitrary text", transform=ax.transAxes)
        # ax.set_title("Avg. Profit of ESPs", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('esp_profit_final.eps')
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
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        ax.plot(x, Random[TERM], '*-', label='Random')
        ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        # ax.set_title("Avg. Number of Served Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('match_final.eps')
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
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        ax.plot(x, Random[TERM], '*-', label='Random')
        ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        # ax.set_title("Avg. Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('ns_profit_final.eps')
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
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        ax.plot(x, Random[TERM], '*-', label='Random')
        ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        # ax.set_title("Avg. Total Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('ns_profit.eps')
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
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        ax.plot(x, Random[TERM], '*-', label='Random')
        ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        # ax.set_title("Avg. Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('ns_profit.eps')
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
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        ax.plot(x, Random[TERM], '*-', label='Random')
        ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        ax.set_title("Social Welfare", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('social_welfare_final.eps')
        plt.show()




if __name__ == '__main__':
    Main()
