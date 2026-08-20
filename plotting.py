import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
import pandas as pd

def plot_multi(df, selection):
    """
    plt
    """
    fig, ax = plt.subplots()

    ax.set_xlabel("Time")
    ax.set_ylabel("Rating")
    
    for team in selection:
        team_data = df[df["team"] == team]
        ax.plot(team_data.index, team_data["rating"], label=team)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncols=4
    )
    
    return fig


def display_results(store_team_results, teams, Nsims):
    # display results direct to terminal
    league_size = len(teams)+1
    for model_name, model_data in store_team_results.items():
        
        
        st.write(f"\nResults for model: {model_name}")
        sorted_data = { k:v for k, v in sorted(model_data.items(), key=lambda item: (item[1]["PTS"]), reverse=True)}

        df = pd.DataFrame.from_dict(sorted_data, orient="index")
        st.write(df)
