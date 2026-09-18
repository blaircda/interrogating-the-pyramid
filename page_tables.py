import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from config import *
from import_process import (
    process_data,
    get_ratings_at_date, split_season_by_date,
    get_table_to_date, get_table_with_elo_to_date, get_season_matchcount_by_date
)
from plotting import display_league_table
from helpers import (
    select_season_range, select_season_division, select_tier_by_season,
    get_sorted_tables, get_teams_by_season_and_div, format_matches_played
)
teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

data = process_data(teams_csv, scores_csv)

teams = data.teams
season_list = data.seasons
season_ratings_start, season_ratings_end = data.season_ratings
ratings_df = data.ratings
scores_df = data.scores 
home_adv = data.home_adv
av_discr = data.home_adv_discr
tables = data.tables
season_league_teams = data.leagues
tiers_by_season = data.tiers

start_season = min(season_list)
end_season = max(season_list) 

st.set_page_config(layout="wide", page_title="Tables | Interrogating the pyramid ")
# control width of content display 
#padl, content, padr = st.columns([0.1,0.8,0.1])

st.header("Tables")
st.write("Historical tables, on any date")
st.write("Caveat: these are calculated from the match results only ignoring points deductions")

sel_season, sel_league = select_season_division(season_list, tiers_by_season, "tab")
sel_teams = get_teams_by_season_and_div(sel_season, sel_league, season_league_teams)

league_size = len(sel_teams)
# initialise their ratings prior to start of season
preseason_ratings = season_ratings_start.loc[sel_season]

# get a breakdown of matches by date  
season_by_date_df = get_season_matchcount_by_date(scores_df, sel_season, sel_league, league_size)
season_gamedays = season_by_date_df["Date"].to_list()

# choose simulation start date
table_date = st.selectbox(
    "Table at date",
    options = season_gamedays,
    index =len(season_gamedays)-1,
    format_func = lambda x: format_matches_played(x, season_by_date_df),
    key = "tab_date_select"
    )

if table_date is not None:
    # split the season fixtures by the date
    matches_played, matches_to_play = split_season_by_date(scores_df, sel_season, sel_league[1], table_date)
    # get initial ratings at that date 
    initial_ratings = get_ratings_at_date(ratings_df, sel_teams, table_date)                
    # display table as of results_to_date
    st.write(f"Table as of {table_date:%Y-%m-%d}")
    table = get_table_with_elo_to_date(ratings_df, scores_df, sel_season, sel_league, table_date, preseason_ratings.loc[sel_teams])
else:
    table = tables.loc[(sel_season,*sel_league)]

display_league_table(table, sel_season)
