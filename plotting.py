import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_multi(df):
    """
    plt each item in items
    """
    fig, ax = plt.subplots()

    ax.set_xlabel("Time")
    ax.set_ylabel("Rating")
    
    ax.plot(df.index, df)

    ax.legend(
        df.columns,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncols=4
    )
    
    return fig
