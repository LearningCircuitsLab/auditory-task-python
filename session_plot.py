import pandas as pd
from lecilab_behavior_analysis.figure_maker import session_summary_figure
from matplotlib.figure import Figure
from village.classes.plot import SessionPlot


class Session_Plot(SessionPlot):
    def __init__(self) -> None:
        super().__init__()

    def create_plot(self, df: pd.DataFrame, df_raw: pd.DataFrame, width: float = 10, height: float = 8) -> Figure:
        # add a dummy session column to the df
        df['session'] = 1
        # get the name of the mouse
        mouse_name = df.subject.iloc[0]
        return session_summary_figure(df, mouse_name=mouse_name, width=width, height=height)
