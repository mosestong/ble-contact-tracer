import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


plots_dir = os.path.join("./", "plots")

def main():
    generate_rssi_distance()

# Creates the graph for rssi vs distance, highlights different conditions with colours
def generate_rssi_distance():
    df = pd.read_csv(os.path.join(plots_dir, 'rssi_vs_distance.csv'))

    conditions = df.groupby('environment')
    for condition, group in conditions:
        plt.scatter(group['distance'], group['rssi'], label=condition)

    plt.legend(title="Environment")
    plt.xlabel("Distance (m)")
    plt.ylabel("RSSI (dBm)")
    plt.title("RSSI vs. Distance")
    plt.savefig(os.path.join(plots_dir, 'rssi_vs_distance.png'))

if __name__ == '__main__':
    main()
