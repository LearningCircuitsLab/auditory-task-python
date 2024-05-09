import time

import matplotlib.pyplot as plt


class TrialPlotter:
    def __init__(self):
        # Initialize the plot
        self.fig, self.ax = plt.subplots()
        self.trial_results = []

    def update_plot(self, result):
        # Append the result to trial_results
        self.trial_results.append(result)
        
        # Update the plot
        self.ax.clear()
        self.ax.plot(self.trial_results, 'o')
        plt.pause(0.01)  # Pause for a short period to allow the plot to update
    
    def keep_plotting(self):
        # Keep the plot open
        plt.show()