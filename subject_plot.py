import pandas as pd
from lecilab_behavior_analysis.figure_maker import subject_progress_figure
from matplotlib.figure import Figure
from village.classes.plot import SubjectPlotFigureManager


class Subject_Plot(SubjectPlotFigureManager):
    def __init__(self) -> None:
        super().__init__()

    def create_plot(self, df: pd.DataFrame, width: float = 10, height: float = 8) -> Figure:
        """
        Overrides the default method to add a calendar
        """
        # TODO: get the mouse name
        return subject_progress_figure(df, title = "subject plot")
