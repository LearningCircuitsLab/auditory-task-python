import pandas as pd
from utils.df_transforms import get_dates_df, get_water_df
from utils.plots import (
    rasterized_calendar_plot,
    trials_by_date_plot,
    trials_by_session_hist,
    water_by_date_plot,
    performance_vs_trials_plot,
)
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec


def trials_by_session_plot(df: pd.DataFrame) -> Figure:
    """
    Information about the trials done in a session and the water consumption
    """
    # create the main figure with GridSpec
    fig = plt.figure(figsize=(10, 9))
    rows_gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 1])
    # Create separate inner grids for each row with different width ratios
    top_gs = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=rows_gs[0])
    med_gs = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=rows_gs[1], width_ratios=[1, 4])
    bot_gs = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=rows_gs[2], width_ratios=[1, 1, 1])
    # Create the top axis spanning both columns
    ax_cal = fig.add_subplot(top_gs[0, 0])
    # Create the medium axes
    ax_bar = fig.add_subplot(med_gs[0, 1])
    ax_hist = fig.add_subplot(med_gs[0, 0])
    # Create the bottom axis
    ax_perf = fig.add_subplot(bot_gs[0, 0])
    # change the width of the ax_perf
    ax_perf.set_position([0.1, 0.1, 0.2, 0.2])

    # generate the dates dataframe
    dates_df = get_dates_df(df)

    # generate the calendar plot
    cal_image = rasterized_calendar_plot(dates_df)
    # paste the calendar plot
    ax_cal.imshow(cal_image)
    ax_cal.axis("off")

    # do the barplot
    ax_bar = trials_by_date_plot(dates_df, ax=ax_bar)

    # Add a vertical histogram
    ax_hist = trials_by_session_hist(dates_df, ax=ax_hist, ylim=ax_bar.get_ylim())

    # overlay water consumption in the bar plot
    water_df = get_water_df(df)
    ax_bar = water_by_date_plot(water_df, ax=ax_bar)

    # Add the performance vs trials plot
    ax_perf = performance_vs_trials_plot(df, ax=ax_perf, legend=False)

    # Adjust the layout
    # plt.subplots_adjust(wspace=0.05)

    return fig
