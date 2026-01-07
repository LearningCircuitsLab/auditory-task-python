import pandas as pd
from lecilab_behavior_analysis.figure_maker import session_summary_figure
from matplotlib.figure import Figure
from village.custom_classes.session_plot_base import SessionPlotBase


class SessionPlot(SessionPlotBase):
    def __init__(self) -> None:
        super().__init__()

    def create_plot(self, df: pd.DataFrame, weight: float = 0.0, width: float = 10, height: float = 8) -> Figure:
        # add a dummy session column to the df
        df['session'] = 1
        # get the name of the mouse
        mouse_name = df.subject.iloc[0]
        return session_summary_figure(df, mouse_name=mouse_name, width=width, height=height)
