import pandas as pd
from matplotlib.figure import Figure
from village.classes.plot import SubjectPlot
from utils.plots import trials_by_session_plot


class Subject_Plot(SubjectPlot):
    def __init__(self) -> None:
        super().__init__()

    def create_plot(self, df: pd.DataFrame) -> Figure:
        """
        Overrides the default method to add a calendar
        """
        return trials_by_session_plot(df)
