import pandas as pd
from lecilab_behavior_analysis.figure_maker import subject_progress_figure
from matplotlib.figure import Figure
from village.custom_classes.subject_plot_base import SubjectPlotBase


class SubjectPlot(SubjectPlotBase):
    def __init__(self) -> None:
        super().__init__()

    def create_plot(self, df: pd.DataFrame, summary_df: pd.DataFrame, width: float = 15, height: float = 10) -> Figure:
        """
        Overrides the default method to add a calendar
        """
        return subject_progress_figure(df, width=width, height=height)
