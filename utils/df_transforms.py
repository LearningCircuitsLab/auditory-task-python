import pandas as pd


def get_dates_df(df: pd.DataFrame) -> pd.DataFrame:
    # raise an error if the date column is not present
    if "date" not in df.columns:
        raise ValueError("The dataframe must have a date column")
    if "current_training_stage" not in df.columns:
        raise ValueError("The dataframe must have a current_training_stage column")
    dates_df = df.groupby(["date", "current_training_stage"]).count().reset_index()
    # set as index the date
    dates_df.set_index("date", inplace=True)
    dates_df.index = pd.to_datetime(dates_df.index)
    return dates_df


def get_water_df(df: pd.DataFrame) -> pd.DataFrame:
    # raise an error if the date column is not present
    if "date" not in df.columns:
        raise ValueError("The dataframe must have a date column")
    if "water" not in df.columns:
        raise ValueError("The dataframe must have a water column")
    water_df = df.groupby("date")["water"].sum()
    return water_df
