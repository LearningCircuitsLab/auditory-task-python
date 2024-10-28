import ast

import matplotlib.pyplot as plt
import pandas as pd


class TrialPlotter:
    def __init__(self):
        # Initialize the plot
        self.fig, self.ax = plt.subplots()
        self.results: pd.DataFrame = pd.DataFrame()
        self.beautify_plot()
    
    def beautify_plot(self):
        # add a title
        self.ax.set_title("Performance")
        # change ticks of the y axis
        self.ax.set_yticks([0, 1])
        # change the labels of the y axis
        self.ax.set_yticklabels(["Error", "Correct"])
        # add another y axis to the right
        self.ax2 = self.ax.twinx()

    # def update_plot(self, result, update_interval=5):
    #     # Append the result to trial_results
    #     self.trial_results.append(result)
        
    #     # Update the plot
    #     if len(self.trial_results) % update_interval == 0:
    #         self.paint_plot()

    def update_plot(self, data):
        # Update data
        self.results = [ast.literal_eval(x) for x in data.correct.values]
        # Update the plot
        self.paint_plot()
    
    def paint_plot(self):
        self.ax.clear()
        self.ax.plot(self.results, '.')
        # plot the mean of the last 5 trials
        self.ax.plot(pd.Series([int(x) for x in self.results]).rolling(5).mean(), 'r')
        # self.beautify_plot()
        plt.pause(0.01)  # Pause for a short period to allow the plot to update
    
    def keep_plotting(self):
        self.ax.clear()
        self.paint_plot()
        plt.pause(0.01)
        # Keep the plot open
        plt.show()