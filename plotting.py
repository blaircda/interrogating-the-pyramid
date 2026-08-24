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

def plot_multi_cols(df, selection, labels={}):
    """
    plt
    """
    fig, ax = plt.subplots()

    #ax.set_xlabel("Time")
    #ax.set_ylabel("")

    for col in selection:
        col_data = df[col]
        ax.plot(col_data.index, col_data, label=labels.get(col, col))

    ax.tick_params(axis='x', labelrotation=90)
    ax.set_xticks(col_data.index[::10])
    ax.legend(
        #loc="upper center",
        #bbox_to_anchor=(0.5, -0.1),
        #ncols=4
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

    table = actual_table.sort_values(by="POS")
    
    if season < change_to_goal_diff:
        display_columns = ["POS", "W", "D", "L", "GF", "GA", "GAv", "PTS"]
    else:
        display_columns = ["POS", "W", "D", "L", "GF", "GA", "GD", "PTS"]

    st.write("Actual results:")
    st.write(table[display_columns])

   
def display_errors(model_errors):
    
    for model_name, model_error_data in model_errors:
        st.write(f"\nErrors for model: {model_name}")
       
        posn_mae, posn_log, points_mae, points_rmse =   model_error_data["posn_mae"], model_error_data["posn_log"], model_error_data["points_mae"], model_error_data["points_rmse"]

        st.write(f"Position Mean Absolute Error: {posn_mae:.2f}")
        st.write(f"Position Log Loss Error: {posn_log:.2f}")
        st.write(f"Points Mean Absolute Error: {points_mae:.2f}")
        st.write(f"Points Root Mean Squared Error: {points_rmse:.2f}")

        
