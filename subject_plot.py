import pandas as pd
from matplotlib.figure import Figure
from village.classes.plot import SubjectPlot
from lecilab_behavior_analysis.figure_maker import subject_progress_figure


class Subject_Plot(SubjectPlot):
    def __init__(self) -> None:
        super().__init__()

    def create_plot(self, df: pd.DataFrame) -> Figure:
        """
        Overrides the default method to add a calendar
        """
        # TODO: get the mouse name
        return subject_progress_figure(df)
