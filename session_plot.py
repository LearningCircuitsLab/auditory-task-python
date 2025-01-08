import pandas as pd
from matplotlib.figure import Figure
from village.classes.plot import SessionPlot
from lecilab_behavior_analysis.figure_maker import session_summary_figure


class Session_Plot(SessionPlot):
    def __init__(self) -> None:
        super().__init__()

    def create_plot(self, df: pd.DataFrame, df_raw: pd.DataFrame) -> Figure:
        return session_summary_figure(df)
