import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
import pandas as pd
import numpy as np
from config import *

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
        cols = ["PTS", "W", "D", "L", "GF", "GA"]
        df[cols] /= Nsims
        pos_cols = df.columns[df.columns.map(lambda x: isinstance(x, int))]
        df[pos_cols] = df[pos_cols]/Nsims
        df["xPOS"] = sum( pos * df[pos] for pos in pos_cols )
        st.write(df[["xPOS"] + cols + pos_cols.tolist() ])

def display_actual_results(actual_table, season):
    if season < change_to_goal_diff:
        display_columns = ["POS", "W", "D", "L", "GF", "GA", "GAv", "PTS"]
    else:
        display_columns = ["POS", "W", "D", "L", "GF", "GA", "GD", "PTS"]

    st.write("Actual results:")
    st.write(actual_table[display_columns])

def get_errors(actual_table, simulation_results, Nsims):
    
    for model_name, model_data in simulation_results.items():
        st.write(f"\nErrors for model: {model_name}")
        df = pd.DataFrame.from_dict(model_data, orient="index")
        cols = ["PTS", "W", "D", "L", "GF", "GA"]
        df[cols] /= Nsims
        pos_cols = df.columns[df.columns.map(lambda x: isinstance(x, int))]
        df[pos_cols] = df[pos_cols]/Nsims
        df["xPOS"] = sum( pos * df[pos] for pos in pos_cols )
        new_col_names = { c: "x"+c for c in cols }
        df = df.rename(columns=new_col_names)
        df["POS"] = actual_table["POS"]
        df["PTS"] = actual_table["PTS"]

        st.write(df[["POS", "xPOS", "PTS", "xPTS"]])

        # posn errors
        posn_mae = (df["POS"] - df["xPOS"]).abs().mean()
        df["log_err"] = -np.log( df.apply(lambda row: row[row["POS"]], axis=1) )
        posn_log = df["log_err"].mean()
        # points errors
        points_mae = (df["PTS"] - df["xPTS"]).abs().mean()
        points_rmse = np.sqrt( ( (df["PTS"] - df["xPTS"]) ** 2).mean() )

        st.write(f"Position Mean Absolute Error: {posn_mae:.2f}")
        st.write(f"Position Log Loss Error: {posn_log:.2f}")
        st.write(f"Points Mean Absolute Error: {points_mae:.2f}")
        st.write(f"Points Root Mean Squared Error: {points_rmse:.2f}")

        

        
