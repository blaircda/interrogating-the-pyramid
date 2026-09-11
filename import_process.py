import csv
import pandas as pd
import numpy as np
import streamlit as st
from collections import defaultdict
from dataclasses import dataclass
from rating_model import (get_new_ratings, w_to_diff)
from config import *

# dataclass to store the processed data
@dataclass
class HistoricalData:
    teams: list
    seasons: list
    season_ratings: tuple[pd.Series, pd.Series]
    ratings: pd.DataFrame
    scores: pd.DataFrame
    home_adv: pd.DataFrame
    home_adv_discr: list
    tables: pd.DataFrame
    leagues: pd.DataFrame
    tiers: pd.DataFrame

@st.cache_data
def process_data( teams_csv, scores_csv ) -> HistoricalData:
    """
    read csv files and process for use
    """
    # import all teams and set their default rating
    teams = pd.read_csv(teams_csv, usecols=["Team"])["Team"].to_list()
    initial_ratings = {team:default_rating for team in teams}
    initial_ratings["home_adv"] = initial_home_adv

    # build full ratings - direct from csv
    ratings, season_ratings, home_success, home_winex = build_ratings(initial_ratings, scores_csv)

    # df of full ratings date by date
    ratings_df = pd.DataFrame.from_dict(ratings).set_index('date') 
    ratings_df.index = pd.to_datetime(ratings_df.index)
    # dfs of ratings at season start/end
    season_ratings_df = pd.DataFrame.from_dict(season_ratings)
    season_ratings_start = (
        season_ratings_df
        .set_index('season_start')
        .drop(columns="season_end")
        .stack()
        .rename("Rstart")   
    )
    season_ratings_end = (
        season_ratings_df
        .dropna(subset=["season_end"])  
        .set_index('season_end')
        .drop(columns="season_start")
        .stack()
        .rename("Rend")
    )

    # compute averages of home success (from actual results) and model home win expectancy
    # and their discrepancy 
    accum_home_success = np.cumsum(home_success)
    av_accum_home_success = [ x/(i+1) for i,x in enumerate(accum_home_success)]
    accum_home_winex = np.cumsum(home_winex)
    av_accum_home_winex  = [ x/(i+1) for i,x in enumerate(accum_home_winex )]
    av_discr = [x-y for x,y in zip(av_accum_home_success,av_accum_home_winex)]

    # read scores_csv into df
    scores_df = pd.read_csv(scores_csv)
    season_list = list(scores_df["Season"].unique())
    season_league_teams = get_seasons_tiers_teams(scores_df)
    tiers_by_season = get_seasons_tiers(scores_df).set_index("Season")

    # tables
    tables = build_league_tables_with_ratings(scores_df, season_ratings_start, season_ratings_end)

    # home advantage
    home_adv = build_home_adv(scores_df)

    return HistoricalData(
        teams = teams,
        seasons = season_list,
        season_ratings = (season_ratings_start, season_ratings_end),
        ratings = ratings_df,
        scores = scores_df,
        home_adv = home_adv,
        home_adv_discr = av_discr,
        tables = tables,
        tiers = tiers_by_season,
        leagues = season_league_teams
    )

@st.cache_data
def build_ratings(live_ratings, scores_csv):
    """
    given initial ratings as dict live_ratings
    and match results in scores_csv
    iterates through the results and records all rating changes
    """
    # container to save every rating update
    rating_history = []

    # container to save ratings at end of each of season
    season_ratings = []

    # containers to track home adv
    home_success = []
    home_winex = []
    home_res_hash = { "H": 1, "D": 0.5, "A": 0}
    N = N_matches_home_adv
    # counters if updating every X games rather than seasonally
    #update_home_adv_counter = 0
    #when_update_home_adv = 100   

    with open(scores_csv, newline="") as f:
        reader = csv.DictReader(f)
        #Date,Season,HomeTeam,AwayTeam,Score,hGoal,aGoal,Division,Tier,Result

        # initialise current_season to none
        current_season = None

        for row in reader:
            date = row["Date"]
            season = row["Season"]

            # on first read set the initial season
            if current_season is None:
                current_season = season
                snapshot = { "season_end": None, "season_start": season } | live_ratings
                season_ratings.append( snapshot ) 

            # check if we have reached a new season
            if season != current_season:

                # update the model home advantage
                # using previous N matches 
                if len(home_success) > N:
                    # update home adv and save end of season ratings
                    #print(f"\n{current_season} home adv: ", live_ratings["home_adv"])

                    av_home_success = round(sum(home_success[-N:])/N,5)
                    av_home_winex = round( sum(home_winex[-N:])/N,5)
                    discr = w_to_diff[int(100000*av_home_success)] - w_to_diff[int(100000*av_home_winex)]
                    live_ratings["home_adv"] += np.round(discr,0).astype(int)

                    #print("Average home success vs win ex:",av_home_success, av_home_winex)
                    #print("Corresponding diffs", w_to_diff[int(100000*av_home_success)], w_to_diff[int(100000*av_home_winex)])
                    #print(f"{season} home adv: ", live_ratings["home_adv"])

                # save the end of season ratings and model home advantage
                snapshot = { "season_end": current_season, "season_start": season } | live_ratings
                season_ratings.append( snapshot ) 

                # set current_season to the nwe season
                current_season = season

            # alternatively update home_adv every X matches
            #if len(home_success) > N and update_home_adv_counter == when_update_home_adv:
            #        pass
            #        av_home_success = round(sum(home_success[-N:])/N,5)
            #        av_home_winex = round( sum(home_winex[-N:])/N,5)
            #        discr = w_to_diff[int(100000*av_home_success)] - w_to_diff[int(100000*av_home_winex)]
            #        live_ratings["home_adv"] += np.round(discr,0).astype(int)
            #        update_home_adv_counter = 0 

            # match details
            home_team = row["HomeTeam"]
            away_team = row["AwayTeam"]
            home_score = int(row["hGoal"])
            away_score = int(row["aGoal"])
            division = row["Division"]

            # get new ratings for the teams involved
            rating_home_new, rating_away_new, win_ex_home = get_new_ratings(live_ratings, home_team, away_team, home_score, away_score)
            rating_history.append( { "date": date,  "season": season, "team": home_team, "rating": rating_home_new, "division": division} )
            rating_history.append( { "date": date, "season": season, "team": away_team, "rating": rating_away_new, "division": division} )
            # update live rating 
            live_ratings[home_team] = rating_home_new
            live_ratings[away_team] = rating_away_new 
            # record the actual home result and its predicted win expectancy
            home_success.append( home_res_hash[row["Result"]] )
            home_winex.append(win_ex_home)

            #update_home_adv_counter += 1
            
    return rating_history, season_ratings, home_success, home_winex


def build_partial_ratings(live_ratings, matches):
    """
    given initial ratings as dict live_ratings
    and match results in dict matches
    iterates through the results and returns the final rating changes

    this is used to "fast forward" ratings to a given point in the season
    """
    for (home_team, away_team), (home_score, away_score) in matches.items():
        # get new ratings for the teams involved
        rating_home_new, rating_away_new, _ = get_new_ratings(live_ratings, home_team, away_team, home_score, away_score)
        # update live rating 
        live_ratings[home_team] = rating_home_new
        live_ratings[away_team] = rating_away_new 

    return live_ratings

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
    home_results = home_results.rename(columns={'A': 'LH', 'D': 'DH', 'H': 'WH'})
    home_results.rename_axis(index={home_results.index.names[-1]: 'Team'}, inplace=True)
    # deal with edge case if not all results have accumulated yet
    for c in [ "WH", "DH", "LH"]:
        home_results[c] = home_results.get(c,0)
        
    # get all teams away results
    away_results = df.groupby(["Season", "Tier", "Division", "AwayTeam"])["Result"].value_counts().unstack(fill_value=0)
    away_results = away_results.rename(columns={'A': 'WA', 'D': 'DA', 'H': 'LA'})
    away_results.rename_axis(index={away_results.index.names[-1]: 'Team'}, inplace=True)
    # deal with edge case if not all results have accumulated yet
    for c in [ "WA", "DA", "LA"]:
        away_results[c] = away_results.get(c,0)
        
    # combine home and away
    full_results = pd.concat([home_results, away_results[["WA", "DA", "LA"]]], axis=1)
    for c in [ "W", "D", "L"]:
        full_results[c] = full_results[[ c+"H", c+"A"]].sum(axis=1)
            
    # get all teams goals for and against at home
    home_results_goals = df.groupby(["Season", "Tier", "Division", "HomeTeam"])[["hGoal", "aGoal"]].sum()
    home_results_goals = home_results_goals.rename(columns={'hGoal': 'GFH', 'aGoal': 'GAH'})
    home_results_goals.rename_axis(index={home_results_goals.index.names[-1]: 'Team'}, inplace=True)

    # get all teams goals against and for away
    away_results_goals = df.groupby(["Season", "Tier", "Division", "AwayTeam"])[["hGoal", "aGoal"]].sum()
    away_results_goals = away_results_goals.rename(columns={'hGoal': 'GAA', 'aGoal': 'GFA'})
    away_results_goals.rename_axis(index={away_results_goals.index.names[-1]: 'Team'}, inplace=True)

    # combine them
    full_results_goals = pd.concat([home_results_goals, away_results_goals[["GFA", "GAA"]]], axis=1).fillna(0)
    full_results_goals["GF"] = full_results_goals[["GFH", "GFA"]].sum(axis=1)
    full_results_goals["GA"] = full_results_goals[["GAH", "GAA"]].sum(axis=1)
    
    # now build full table
    full_tables = pd.concat([full_results, full_results_goals], axis=1)
    full_tables["GD"] = full_tables["GF"] - full_tables["GA"]
    full_tables["GAv"] = full_tables["GF"] / full_tables["GA"]

    # take into account historical rules
    seasons = full_tables.index.get_level_values("Season")
    
    two_point_era = full_tables[ seasons < change_to_three_points_per_win ]
    if not two_point_era.empty:
        two_point_era["PTS"] = 2*full_tables["W"] + full_tables["D"]
        two_point_era["PTS_RULE"] = 2

    three_point_era = full_tables[ seasons >= change_to_three_points_per_win ]
    if not three_point_era.empty:
        three_point_era["PTS"] = 3*full_tables["W"] + full_tables["D"]
        three_point_era["PTS_RULE"] = 3

    full_tables = pd.concat([two_point_era, three_point_era])
    
    goal_average_era = full_tables[seasons < change_to_goal_diff].sort_values(["PTS", "GAv", "GF"], ascending=[False, False, False])
    goal_diff_era = full_tables[ seasons >= change_to_goal_diff ].sort_values(["PTS", "GD", "GF"], ascending=[False, False, False])

    full_tables = pd.concat([goal_average_era, goal_diff_era])

    full_tables["GOAL_RULE"] = "Diff"
    full_tables.loc[seasons < change_to_goal_diff, "GOAL_RULE"] = "Av"

    # add a position column 
    full_tables["POS"] = full_tables.groupby(level=["Season", "Tier", "Division"]).cumcount().add(1)
    # add an absolute pyramid position column
    # between 1921 and 1958 there are 2 tier 3 divisions
    # order by position and then tie break by points, goal av, goal for
    full_tables = full_tables.sort_values(by=["Tier", "POS", "PTS", "GAv", "GF"], ascending=[True, True, False, False, False])
    full_tables["POSPyr"] = full_tables.groupby(level=["Season"]).cumcount().add(1)

    # per game stats
    full_tables["MP"] = full_tables["W"] + full_tables["D"] + full_tables["L"]
    cols = ["GF", "GA", "PTS", "W", "D", "L"]
    full_tables[[f"{c}pg" for c in cols]] = full_tables[cols].div(full_tables["MP"], axis=0)
    # home/away per game stats
    cols = ["WH", "DH", "LH", "WA", "DA", "LA", "GFH", "GAH", "GFA", "GAA"]
    full_tables[[f"{c}pg" for c in cols]] = full_tables[cols].mul(2).div(full_tables["MP"], axis=0)
    full_tables["Gpg"] = full_tables[["GFpg", "GApg"]].sum(axis=1)
    
    full_tables = full_tables.sort_index()
    return full_tables

@st.cache_data
def build_league_tables_with_ratings(scores_df, season_ratings_start, season_ratings_end):
    """
    build league tables and add rating information
    """
    tables = build_league_tables(scores_df)
    tables = (
        tables
        .join(season_ratings_start, on=["Season", "Team"])
        .join(season_ratings_end, on=["Season", "Team"])
    )
    tables["Rstart"] = tables["Rstart"].astype("Int64")
    tables["Rend"] = tables["Rend"].astype("Int64")
    tables["Rchange"] = tables["Rend"] - tables["Rstart"]

    # difference vs max rating in league
    tables["Rbelow_start"] = (
            tables["Rstart"]
            - tables.groupby(level=["Season", "Tier", "Division"])["Rstart"].transform("max")
    )
    tables["Rbelow_end"] = (
        tables["Rend"]
        - tables.groupby(level=["Season", "Tier", "Division"])["Rend"].transform("max")
    )

    # rank in league by rating
    tables["Rstart_rank"] = (
        tables.groupby(["Season", "Tier", "Division"])["Rstart"]
        .rank(method="min", ascending=False).astype("Int64")
    )
    tables["Rend_rank"] = (
        tables.groupby(["Season", "Tier", "Division"])["Rend"]
        .rank(method="min", ascending=False).astype("Int64")
    )
    tables["Rrank_change"] = tables["Rstart_rank"] - tables["Rend_rank"]

    # rank in pyramid by rating
    tables["RPyr_start"] = tables.groupby(level=["Season"])["Rstart"].rank("min", ascending=False)
    tables["RPyr_end"] = tables.groupby(level=["Season"])["Rend"].rank("min", ascending=False)
    tables["RPyr_change"] = tables["RPyr_start"] - tables["RPyr_end"]

    return tables

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
    filtered = ratings_df[
        ratings_df["team"].isin(teams) &
        (ratings_df.index <= date)
    ].sort_index()

    return (
        filtered.groupby("team")["rating"]
        .last()
        .astype(int)
        .to_dict()
    )

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
    return  build_league_tables(df).loc[(season, *league)]

def get_table_with_elo_to_date(ratings_df, scores_df, season, league, date, initial_ratings):
    """
    for specified season and league (division)
    return the table based on results up to and including date
    including the ELO ratings
    """
    table = get_table_to_date(scores_df, season, league, date)

    table["Rstart"] = initial_ratings
    
    rats = get_ratings_at_date(ratings_df, table.index.to_list(), date)
    table["Rend"] = pd.Series(rats)
    return table
    
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
