import pandas as pd
import streamlit as st
from config import *

#Date,Season,HomeTeam,AwayTeam,Score,hGoal,aGoal,Division,Tier,Result

@st.cache_data
def get_seasons_daterange(scores_df):
    """
    returns a dataframe with the start/end dates of each season
    """
    df = scores_df.groupby(["Season"]).agg(
    start=("Date", "min"),
    end=("Date", "max")
    )
    return df

@st.cache_data
def get_seasons_tiers(scores_df):
    """
    returns a dataframe with the tier/divisions for each season
    """
    df = scores_df[["Season", "Tier", "Division"]].drop_duplicates()
    return df

@st.cache_data
def get_seasons_tiers_teams(scores_df):
    """
    returns a dataframe with the teams for each season in each tier/division
    """
    # need to catch an edge case where if only one round of games has been played you need to know all the teams
    df = scores_df[["Season", "Tier", "Division", "HomeTeam", "AwayTeam"]]
    df = df.groupby(["Season", "Tier", "Division"]).apply(lambda g: pd.unique(g[["HomeTeam", "AwayTeam"]].values.ravel()).tolist())
    return df

@st.cache_data
def build_league_tables(df):
    """
    constructs league tables from a df containing results
    """
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

    # deals with edge case where table is being built for small number of opening fixtures and not all results have occured
    for c in [ "W", "D", "L"]:
        full_results[c] = full_results.get( c, 0 )
    
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
    if not two_point_era.empty:
        two_point_era["PTS"] = 2*full_tables["W"] + full_tables["D"]

    three_point_era = full_tables[ seasons >= change_to_three_points_per_win ]
    if not three_point_era.empty:
        three_point_era["PTS"] = 3*full_tables["W"] + full_tables["D"]

    full_tables = pd.concat([two_point_era, three_point_era])
    
    goal_average_era = full_tables[seasons < change_to_goal_diff].sort_values(["PTS", "GAv", "GF"], ascending=[False, False, False])
    goal_diff_era = full_tables[ seasons >= change_to_goal_diff ].sort_values(["PTS", "GD", "GF"], ascending=[False, False, False])

    full_tables = pd.concat([goal_average_era, goal_diff_era])

    # add a position column 
    full_tables["POS"] = full_tables.groupby(level=["Season", "Tier", "Division"]).cumcount().add(1)
    full_tables = full_tables.sort_index()
    return full_tables

@st.cache_data
def build_home_adv(df):
    """
    returns a dataframe with aggregated season-by-season home results average
    """
    # get all teams home results
    home_results = df.groupby(["Season"])["Result"].value_counts().unstack(fill_value=0)
    home_results = home_results.rename(columns={'A': 'L', 'D': 'D', 'H': 'W'})
    #home_results.rename_axis(index={home_results.index.names[-1]: 'Team'}, inplace=True)
    home_results["HomeGames"] = home_results["W"] + home_results["D"] + home_results["L"]
    home_results["HomeSuccess"] = home_results["W"] + 0.5*home_results["D"]
    home_results["AvHomeSuccess"] = home_results["HomeSuccess"] / home_results["HomeGames"]
    home_results["AvHomeWins"] = home_results["W"] / home_results["HomeGames"]

    #home_results = home_results.unstack(level=0, fill_value=0)
    return home_results

def get_ratings_at_date(ratings_df, teams, date):
    """
    return dict of latest ratings of teams at date
    """
    filtered = ratings_df[ (ratings_df["team"].isin(teams))  & (ratings_df.index <= date)]

    ratings_at_date = {}
    for team in teams:
        ratings_at_date[team] = int(filtered[(filtered["team"]==team)].iloc[-1]["rating"])

    return ratings_at_date

def split_season_by_date(scores_df, season, league, date):
    """
    for specified season and league (division)
    return the results of matches up to and including date
    plus the remaining fixtures without the result
    """
    matches_played = {}
    matches_to_play = []

    df = scores_df[ (scores_df["Season"] == season) & (scores_df["Division"] == league) ]
    df["Date"] = pd.to_datetime(df["Date"])

    played = df[ df["Date"] <= date ][["HomeTeam", "AwayTeam", "hGoal", "aGoal"]].to_dict(orient='records')
    for match in played:
        matches_played[ ( match["HomeTeam"], match["AwayTeam"] ) ] = ( match["hGoal"], match["aGoal"] )

    matches_to_play = list(df[ df["Date"] > date ][["HomeTeam", "AwayTeam"]].itertuples(index=False, name=None))
    
    return matches_played, matches_to_play

def split_season_by_percent(scores_df, season, league, percent):
    """
    for specified season and league (division)
    return the results of first percent matches
    plus the remaining fixtures without the result
    """
    matches_played = {}
    matches_to_play = []

    df = scores_df[ (scores_df["Season"] == season) & (scores_df["Division"] == league) ]
    N = int(len(df)*percent/100)

    played = df.iloc[:N][["HomeTeam", "AwayTeam", "hGoal", "aGoal"]].to_dict(orient='records')
    for match in played:
        matches_played[ ( match["HomeTeam"], match["AwayTeam"] ) ] = ( match["hGoal"], match["aGoal"] )

    matches_to_play = list(df.iloc[N:][["HomeTeam", "AwayTeam"]].itertuples(index=False, name=None))
    
    return matches_played, matches_to_play

def get_table_to_date(scores_df, season, league, date):
    """
    for specified season and league (division)
    return the table based on results up to and including date
    """
    df = scores_df[  (scores_df["Season"] == season) & (scores_df["Division"] == league[1]) ]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[ (df["Date"] <= date) ]
    return build_league_tables(df).loc[(season, *league)]

def get_season_matchcount_by_date(scores_df, season, league, league_size):
    """
    returns a dataframe of the dates of gamedays and the number of games played
    for specified season and league (division)
    """
    number_matches = league_size*(league_size - 1)
    df = scores_df[ (scores_df["Season"] == season) & (scores_df["Division"] == league[1]) ]
    df = df.groupby("Date").size().reset_index(name="MatchesOnDate")
    df["MatchesPlayed"] = df["MatchesOnDate"].cumsum()
    df["MatchesPlayedPercent"] = 100*df["MatchesPlayed"]/number_matches
    df["Date"] = pd.to_datetime(df["Date"])
    return df
