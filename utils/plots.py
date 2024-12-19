import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import calplot
import numpy as np
import seaborn as sns


def rasterized_calendar_plot(dates_df: pd.DataFrame) -> np.ndarray:
    # make the calendar plot and convert it to an image
    if "trial" not in dates_df.columns:
        raise ValueError("The dataframe must have a trial column")
    cpfig, _ = calplot.calplot(
        data=dates_df.trial, yearlabel_kws={"fontname": "sans-serif"}
    )
    canvas = FigureCanvasAgg(cpfig)
    canvas.draw()
    width, height = cpfig.get_size_inches() * cpfig.get_dpi()
    image = np.frombuffer(canvas.tostring_rgb(), dtype="uint8").reshape(
        int(height), int(width), 3
    )
    plt.close(cpfig)
    return image


def trials_by_date_plot(dates_df: pd.DataFrame, ax: plt.Axes = None) -> plt.Axes:
    if "trial" not in dates_df.columns:
        raise ValueError("The dataframe must have a [trial] column")
    if dates_df.index.name != "date":
        raise ValueError("The dataframe must have [date] as index")
    if ax is None:
        ax = plt.gca()
    if "current_training_stage" in dates_df.columns:
        hue = "current_training_stage"
    else:
        hue = None
    sns.barplot(data=dates_df, x="date", y="trial", hue=hue, ax=ax)
    ax.legend(bbox_to_anchor=(0.5, 1.25), loc="upper center", ncol=3, borderaxespad=0.0)
    ax.get_legend().get_frame().set_linewidth(0.0)
    ax.set_ylabel("Number of trials")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return ax


def trials_by_session_hist(
    dates_df: pd.DataFrame, ax: plt.Axes = None, **kwargs
) -> plt.Axes:
    if "trial" not in dates_df.columns:
        raise ValueError("The dataframe must have a trial column")
    dates_df["trial"].hist(ax=ax, orientation="horizontal", bins=15, color="gray")
    if "ylim" in kwargs:
        ax.set_ylim(kwargs["ylim"])
    # remove the axis
    ax.axis("off")
    # flip x axis
    ax.invert_xaxis()
    return ax


def performance_vs_trials_plot(df: pd.DataFrame, ax: plt.Axes = None, **kwargs) -> plt.Axes:
    """
    Plot the performance vs the number of trials
    """
    if ax is None:
        ax = plt.gca()

    # sort the df by "session" and "trial"
    df = df.sort_values(["session", "trial"])
    # add a column with the total number of trials
    df["total_trial"] = np.arange(1, df.shape[0] + 1)

    # TODO: do this for each session, preprocessing
    # calculate the performance as a mean of the last 25 trials
    df["performance_25"] = df.correct.rolling(window=25).mean() * 100
    # plot the performance
    for stage in df["current_training_stage"].unique():
        stage_df = df[df["current_training_stage"] == stage]
        sns.lineplot(
            data=stage_df, x="total_trial", y="performance_25", ax=ax, label=stage
        )
    ax.set_xlabel("Trial number")
    ax.set_ylabel("Performance")
    # horizontal line at 50%
    ax.axhline(50, linestyle="--", color="gray")
    # remove box
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if "legend" in kwargs:
        if kwargs["legend"] == False:
            ax.get_legend().remove()

    return ax


def water_by_date_plot(water_df: pd.Series, ax: plt.Axes = None) -> plt.Axes:
    if ax is None:
        ax = plt.gca()
    if water_df.index.name != "date":
        raise ValueError("The dataframe must have [date] as index")
    # check if there is someting plotted in the axis already
    items_in_axis = (
        len(ax.patches) + len(ax.lines) + len(ax.collections) + len(ax.texts)
    )
    if items_in_axis > 0:
        # create a new y axis on the right
        ax2 = ax.twinx()
        ax_to_use = ax2
        add_stuff = False
    else:
        ax_to_use = ax
        add_stuff = True

    water_df.plot(ax=ax_to_use, color="black")
    ax_to_use.set_ylabel("Water consumed")
    ax_to_use.spines["top"].set_visible(False)
    if add_stuff:
        ax_to_use.set_xlabel("Date")
        ax_to_use.tick_params(axis="x", rotation=45)
        for label in ax_to_use.get_xticklabels():
            label.set_horizontalalignment("right")
        ax_to_use.spines["right"].set_visible(False)
    return ax_to_use
