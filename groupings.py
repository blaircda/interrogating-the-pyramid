import pandas as pd
import streamlit as st
from config import *

#Date,Season,HomeTeam,AwayTeam,Score,hGoal,aGoal,Division,Tier,Result

@st.cache_data
def get_seasons_daterange(scores_file):
    df = pd.read_csv(scores_file, usecols=["Date", "Season"])
    df = df.groupby(["Season"]).agg(
    start=("Date", "min"),
    end=("Date", "max")
    )
    df["pre"] = df["end"].shift(1)
    #print(df)
    return df

@st.cache_data
def get_seasons_tiers(scores_file):
    df = pd.read_csv(scores_file, usecols=["Season", "Tier", "Division"])
    df = df[["Season", "Tier", "Division"]].drop_duplicates()
    #print(df.index)
    return df

@st.cache_data
def get_seasons_tiers_teams(scores_file):
    df = pd.read_csv(scores_file, usecols=["Season", "Tier", "Division", "HomeTeam"])
    df = df.groupby(["Season", "Tier", "Division"])["HomeTeam"].unique().apply(sorted)
    #print(df)
    return df

@st.cache_data
def build_league_tables(scores_file):
    df = pd.read_csv(scores_file)

    # get all teams home results
    home_results = df.groupby(["Season", "Tier", "Division", "HomeTeam"])["Result"].value_counts().unstack(fill_value=0)
    home_results = home_results.rename(columns={'A': 'L', 'D': 'D', 'H': 'W'})
    home_results.rename_axis(index={home_results.index.names[-1]: 'Team'}, inplace=True)

    # get all teams away results
    away_results = df.groupby(["Season", "Tier", "Division", "AwayTeam"])["Result"].value_counts().unstack(fill_value=0)
    away_results = away_results.rename(columns={'A': 'W', 'D': 'D', 'H': 'L'})
    away_results.rename_axis(index={away_results.index.names[-1]: 'Team'}, inplace=True)

    # combine them
    full_results = home_results.add(away_results, fill_value=0)

    # get all teams goals for and against at home
    home_results_goals = df.groupby(["Season", "Tier", "Division", "HomeTeam"])[["hGoal", "aGoal"]].sum()
    home_results_goals = home_results_goals.rename(columns={'hGoal': 'GF', 'aGoal': 'GA'})
    home_results_goals.rename_axis(index={home_results_goals.index.names[-1]: 'Team'}, inplace=True)

    # get all teams goals against and for away
    away_results_goals = df.groupby(["Season", "Tier", "Division", "AwayTeam"])[["hGoal", "aGoal"]].sum()
    away_results_goals = away_results_goals.rename(columns={'hGoal': 'GA', 'aGoal': 'GF'})
    away_results_goals.rename_axis(index={away_results_goals.index.names[-1]: 'Team'}, inplace=True)

    # combine them
    full_results_goals = home_results_goals.add(away_results_goals, fill_value=0)

    # now build full table
    full_tables = pd.concat([full_results, full_results_goals], axis=1)
    full_tables["GD"] = full_tables["GF"] - full_tables["GA"]
    full_tables["GAv"] = full_tables["GF"] / full_tables["GA"]

    # take into account historical rules
    seasons = full_tables.index.get_level_values("Season")
    
    two_point_era = full_tables[ seasons < change_to_three_points_per_win ]
    two_point_era["PTS"] = 2*full_tables["W"] + full_tables["D"]

    three_point_era = full_tables[ seasons >= change_to_three_points_per_win ]
    three_point_era["PTS"] = 3*full_tables["W"] + full_tables["D"]

    full_tables = pd.concat([two_point_era, three_point_era])

    
    goal_average_era = full_tables[seasons < change_to_goal_diff].sort_values(["PTS", "GAv", "GF"], ascending=[False, False, False])
    goal_diff_era = full_tables[ seasons >= change_to_goal_diff ].sort_values(["PTS", "GD", "GF"], ascending=[False, False, False])

    full_tables = pd.concat([goal_average_era, goal_diff_era])

    full_tables["POS"] = full_tables.groupby(level=["Season", "Tier", "Division"]).cumcount().add(1)
    full_tables = full_tables.sort_index()
    return full_tables
    #full_tables.sort_values(by=["PTSold", "GAv"], ascending=[False, False],inplace=True)
    #full_tables.loc["1888/1889"][["W", "D", "L", "GF", "GA", "GD", "GAv", "PTS", "PTSold"]]
    
