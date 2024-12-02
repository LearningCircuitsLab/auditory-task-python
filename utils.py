# TODO: move this to a different package eventually
# something that is used to analyze the data

# alternatively, create a class that is df, and then create methods to analyze the data,
# and to plot the data


def get_session_performance(df, session: int) -> float:
    """
    TODO: move this to a different package
    This method calculates the performance of a session.
    """

    return df[df.session == session].correct.mean()


def get_session_number_of_trials(df, session: int) -> int:
    """
    This method calculates the number of trials in a session.
    """

    return df[df.session == session].shape[0]
