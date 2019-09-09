import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

TERM = "iteration"
Data = ["5","20","35","50","65"]

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
    my = {"ns utility":[], "ns profit":[], "esp profit":[], "ns latency": [], "match": [], "true latency":[], "social":[], "iteration":[]}

    for filename in Data:
        df = pd.read_excel('../deltachange/N50n200m5_d'+filename+'.xlsx')
        # calIter(df["iteration"])
        my["iteration"].append(float(df["iteration"].mean()))
        my["social"].append((calU(df["ns_profit"])+calU(df["esp_utility"])))
        my["ns utility"].append(calU(df["ns_utility"]))
        my["esp profit"].append(calU(df["esp_utility"]))
        my["ns profit"].append(calU(df["ns_profit"]))
        my["ns latency"].append(calL(df["ns_latency"], False))
        my["true latency"].append(calL(df["ns_true_latency"], True))
        my["match"].append(float(df["matched"].mean()))


    if TERM == "esp profit":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Delta')
        ax.set_ylabel('Profit')
        x = np.linspace(5, 65, 5)
        # print(new_ticks)
        ax.set_xticks(x)
        # plt.title("The number of served network services", fontweight='bold', fontsize='x-large',verticalalignment ='center')
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        # ax.plot(x, Random[TERM], '*-', label='Random')
        # ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels ,loc='lower right')
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
        ax.set_xlabel('Delta')
        ax.set_ylabel('Number of Served Network Services')
        x = np.linspace(5, 65, 5)
        # print(new_ticks)
        ax.set_xticks(x)
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        # ax.plot(x, Random[TERM], '*-', label='Random')
        #ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels ,loc='upper right')
        # ax.set_title("Avg. Number of Served Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('match_final.eps')
        plt.show()
    elif TERM == "ns profit":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Delta')
        ax.set_ylabel('Profit')
        x = np.linspace(5, 65, 5)
        # print(new_ticks)
        ax.set_xticks(x)
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        # ax.plot(x, Random[TERM], '*-', label='Random')
        # ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels ,loc='upper right')
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
        x = np.linspace(5, 65, 5)
        # print(new_ticks)
        ax.set_xticks(x)
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        # ax.plot(x, Random[TERM], '*-', label='Random')
        # ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        ax.set_title("Avg. Total Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        # plt.savefig('ns_profit.eps')
        plt.show()
    elif TERM == "true latency":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Numbers of Network Services')
        ax.set_ylabel('Profit')
        x = np.linspace(5, 65, 5)
        # print(new_ticks)
        ax.set_xticks(x)
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        # ax.plot(x, Random[TERM], '*-', label='Random')
        # ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels, bbox_to_anchor=(0.5,-0.28),loc='lower center',ncol=3)
        ax.set_title("Avg. Profit of Network Services", fontsize='x-large', y=1.05)
        plt.tight_layout()
        # plt.savefig('ns_profit.eps')
        plt.show()
    elif TERM == "social":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Delta')
        ax.set_ylabel('Social Welfare')
        x = np.linspace(5, 65, 5)
        # print(new_ticks)
        ax.set_xticks(x)
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        # ax.plot(x, Random[TERM], '*-', label='Random')
        # ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels ,loc='lower right')
        # ax.set_title("Social Welfare", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('social_welfare_final.eps')
        plt.show()
    elif TERM == "iteration":
        plt.gcf().clear()
        plt.style.use('ggplot')
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        ax.set_xlabel('Delta')
        ax.set_ylabel('Iteration')
        x = np.linspace(5, 65, 5)
        # print(new_ticks)
        ax.set_xticks(x)
        ax.plot(x, my[TERM], 'o-', label='BP-DNSES')
        # ax.plot(x, Random[TERM], '*-', label='Random')
        # ax.plot(x, oneside[TERM],'x-' ,label='CHA')
        handles, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(handles, labels ,loc='upper right')
        # ax.set_title("Avg. Iteration", fontsize='x-large', y=1.05)
        plt.tight_layout()
        plt.savefig('iteration_final.eps')
        plt.show()




if __name__ == '__main__':
    Main()
