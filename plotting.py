import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
import pandas as pd
import numpy as np
from config import *

def plot_multi_ratings(df, selection):
    """
    for each team in selection
    returns a combined plot of their historical ratings stored in df
    """
    fig, ax = plt.subplots(figsize=(8,6), constrained_layout=True)

    #ax.set_xlabel("Time")
    ax.set_ylabel("Rating")
    
    for team in selection:
        team_data = df[df["team"] == team]
        ax.plot(team_data.index, team_data["rating"], label=team)

    ax.grid(True, alpha=0.3)
    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncols=4
    )

    return fig

def plot_multi_cols(df, selection, labels={}):
    """
    for each col of df in selection
    returns a combined plot of their data
    with labels specified by optional dict labels 
    """
    fig, ax = plt.subplots(figsize=(8,6), constrained_layout=True)

    #ax.set_xlabel("Time")
    #ax.set_ylabel("")

    for col in selection:
        col_data = df[col]
        ax.plot(col_data.index, col_data, label=labels.get(col, col))

    ax.tick_params(axis='x', labelrotation=90)
    N = max(1, len(col_data.index) // 10)

    ax.set_xticks(col_data.index[::N])
    ax.grid(True, alpha=0.3)

    ax.legend(
        #loc="upper center",
        #bbox_to_anchor=(0.5, -0.1),
        #ncols=4
    )
    
    return fig

def plot_model_home_adv(data):
    fig, ax = plt.subplots(figsize=(8,6), constrained_layout=True)
    ax.plot(data, label="Model home advantage")
    ax.set_xticks(data.index[::10])
    ax.tick_params(axis='x', labelrotation=90)
    ax.grid(True, alpha=0.3)
    ax.legend()        
    return fig

def plot_model_home_adv_compare(data, exclude_games=50):
    # plot comparison between model home win ex and actual home success
    fig, ax = plt.subplots(figsize=(8,6), constrained_layout=True)
    #ax.plot(av_accum_home_success, label="home_success")
    #ax.plot(av_accum_home_winex, label="home win ex")
    ax.plot( data[exclude_games:], label="Actual Home Success - Home Win Ex")
    ax.set_xlabel(f"Number of games (first {exclude_games} excluded)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return fig

def plot_row(row):
    print(row)

def display_results(model_data, teams, Nsims):
    """
    display simulated results
    for each simulation model in store_team_results
    """
    league_size = len(teams)
    sorted_data = { k:v for k, v in sorted(model_data.items(), key=lambda item: (item[1]["PTS"]), reverse=True)}
    df = pd.DataFrame.from_dict(sorted_data, orient="index")
    cols = ["PTS", "W", "D", "L", "GF", "GA"]
    df[cols] /= Nsims
    pos_cols = df.columns[df.columns.map(lambda x: isinstance(x, int))]
    df[pos_cols] = df[pos_cols]/Nsims
    df["xPOS"] = sum( pos * df[pos] for pos in pos_cols )
    st.dataframe(df[["xPOS"] + cols + pos_cols.tolist() ])

    fig, axs = plt.subplots(
                        nrows = league_size//2,
                        ncols = 2,
                        figsize = (10,15),
                        constrained_layout=True
                )
    for team, ax in zip(df.index, axs.flat):
        ax.bar( [n for n in pos_cols], df.loc[team][pos_cols] )
        ax.set_title(f"{team}")
        ax.set_xlim(0, league_size+1)
        ax.set_xticks(list( range(1,league_size+1) ))
        ax.tick_params(axis='x', labelsize=6)
        ax.set_ylim(0,1)
    fig.suptitle("Position probabilities")
    #fig.subplots_adjust(
    #    left = 0,  # the left side of the subplots of the figure
    #    right = 1,   # the right side of the subplots of the figure
    #    bottom = 0.05,  # the bottom of the subplots of the figure
    #    top = 0.95,    # the top of the subplots of the figure
    #    wspace = 0.1,  # the amount of width reserved for space between subplots,
    #    # expressed as a fraction of the average axis width
    #    hspace = 2,  # the amount of height reserved for space between subplots,
    #    # expressed as a fraction of the average axis height
    #)
    st.pyplot(fig,width='stretch')
    plt.close(fig)


def display_league_table(actual_table, season):
    """
    display league table 
    """
    table = actual_table.sort_values(by="POS")
    if season < change_to_goal_diff:
        display_columns = ["POS", "W", "D", "L", "GF", "GA", "GAv", "PTS", "Rstart", "Rend"]
    else:
        display_columns = ["POS", "W", "D", "L", "GF", "GA", "GD", "PTS", "Rstart", "Rend"]
    st.write(table[display_columns])

def display_errors(model_errors):
    st.write(f"\nErrors")
    posn_mae, posn_log, points_mae, points_rmse =   model_errors["posn_mae"], model_errors["posn_log"], model_errors["points_mae"], model_errors["points_rmse"]
    st.write(f"Position Mean Absolute Error: {posn_mae:.2f}")
    st.write(f"Position Log Loss Error: {posn_log:.2f}")
    st.write(f"Points Mean Absolute Error: {points_mae:.2f}")
    st.write(f"Points Root Mean Squared Error: {points_rmse:.2f}")

def plot_season_sim_errors(df):
    x = df.index    
    cols = df.columns
    ncols = len(cols)
    fig, axs = plt.subplots(ncols,1,figsize=(10,20), constrained_layout=True)
    for ax, col in zip(axs, df.columns):
        ax.plot(x, df[col], label=col)
        ax.grid(True, alpha=0.5)
        ax.set_xlabel("Simulation start (percent of season)")
        ax.set_ylabel("Error")
        ax.set_title(col)
    #plt.subplots_adjust(bottom=1, top = 2)
    return fig

def plot_season_sim_errors_multi(df, selection):
    x = df.loc[selection[0]].index
    cols = df.columns
    ncols = len(cols)
    fig, axs = plt.subplots(ncols,1,figsize=(10,20), constrained_layout=True)
    for ax, col in zip(axs, df.columns):
        for sel in selection:
            ax.plot(x, df.loc[sel, col], label=' '.join(sel))
        ax.grid(True, alpha=0.5)
        ax.set_xlabel("Simulation start (percent of season)")
        ax.set_ylabel("Error")
        ax.set_title(col)
        ax.legend()
    #plt.subplots_adjust(bottom=1, top = 2)
    return fig

def plot_season_start_errors(df):
    seasons = df.index.to_flat_index()
    x = ['\n'.join(ssn) for ssn in seasons]
    cols = df.columns
    ncols = len(cols)
    fig, axs = plt.subplots(ncols,1,figsize=(10,20), constrained_layout=True)
    for ax, col in zip(axs, df.columns):
        ax.bar(x, df[col], label=col)
        ax.grid(True, alpha=0.5)
        #ax.set_xlabel("Season")
        ax.set_ylabel("Error")
        ax.set_title(col)
        if len(x) > 4:
            ax.tick_params(axis="x", labelrotation=270)
    #plt.subplots_adjust(bottom=1, top = 2)
    return fig
