import pandas as pd
from lecilab_behavior_analysis.plots import (correct_left_and_right_plot,
                                             side_correct_performance_plot)
from matplotlib import gridspec
from matplotlib import pyplot as plt
from village.custom_classes.online_plot_base import OnlinePlotBase


class OnlinePlot(OnlinePlotBase):
    # TODO: make this nice and add something informative for habituation, like the side chosen
    def __init__(self) -> None:
        super().__init__()
        self.fig = plt.figure(figsize=(20, 5))
        rows_gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])
        # Create separate inner grids for each row with different width ratios
        top_gs = gridspec.GridSpecFromSubplotSpec(
            1, 1, subplot_spec=rows_gs[0]
        )
        bot_gs = gridspec.GridSpecFromSubplotSpec(
            1, 3, subplot_spec=rows_gs[1], width_ratios=[1, 1, 1]
        )
        self.ax1 = self.fig.add_subplot(top_gs[0, 0])
        self.ax2 = self.fig.add_subplot(bot_gs[0, 0])
        self.ax3 = self.fig.add_subplot(bot_gs[0, 1])

    def update_plot(self, df: pd.DataFrame) -> None:
        try:
            self.make_timing_plot(df, self.ax3)
        except Exception:
            self.make_error_plot(self.ax3)
        try:
            self.ax1.clear()
            self.ax1 = side_correct_performance_plot(df, self.ax1, 50)
        except Exception as e:
            print(e)
            self.make_error_plot(self.ax1)
        try:
            self.ax2.clear()
            self.ax2 = correct_left_and_right_plot(df, self.ax2)
        except Exception as e:
            print(e)
            self.make_error_plot(self.ax2)

        self.fig.tight_layout()

    def make_timing_plot(self, df: pd.DataFrame, ax: plt.Axes) -> None:
        ax.clear()
        df.plot(kind="scatter", x="TRIAL_START", y="trial", ax=ax)

    def make_error_plot(self, ax) -> None:
        ax.clear()
        ax.text(
            0.5,
            0.5,
            "Could not create plot",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
        )
