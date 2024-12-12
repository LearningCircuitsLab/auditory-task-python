# TODO: move this to a different package eventually
# something that is used to analyze the data

# alternatively, create a class that is df, and then create methods to analyze the data,
# and to plot the data

import numpy as np


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


def get_block_size_truncexp_mean30() -> int:
    """
    This method returns a block size following a truncated exponential distribution.
    Optimized to get the mean of the distribution to be 30 using ChatGPT.
    """
    lower_bound = 20
    upper_bound = 50
    optimal_lambda = 0.0607
    u = np.random.uniform(0, 1)  # Uniform sample
    block_size = lower_bound - np.log(1 - u * (1 - np.exp(-optimal_lambda * (upper_bound - lower_bound)))) / optimal_lambda

    return int(block_size)
