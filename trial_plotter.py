import matplotlib.pyplot as plt


class TrialPlotter:
    def __init__(self):
        # Initialize the plot
        self.fig, self.ax = plt.subplots()
        self.trial_results = []

    def update_plot(self, result, update_interval=5):
        # Append the result to trial_results
        self.trial_results.append(result)
        
        # Update the plot
        if len(self.trial_results) % update_interval == 0:
            self.ax.clear()
            self.ax.plot(self.trial_results, 'o')
            plt.pause(0.01)  # Pause for a short period to allow the plot to update
    
    def keep_plotting(self):
        self.ax.clear()
        self.ax.plot(self.trial_results, 'o')
        plt.pause(0.01)
        # Keep the plot open
        plt.show()