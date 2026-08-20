import csv
import pandas as pd
import streamlit as st
from plotting import *
from import_process import *
from groupings import *

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

teams, ratings, ratings_by_team = build_ratings(teams_csv, scores_csv)

ratings_df = pd.DataFrame.from_dict(ratings, orient="index")
ratings_df.index = pd.to_datetime(ratings_df.index)

ratings_by_team_df = pd.DataFrame.from_dict(ratings_by_team, orient="index")

st.set_page_config(layout="wide", page_title="Interrogating the pyramid")
col1, col2, col3 = st.columns([0.1,0.8,0.1])

with col2:
    mt1, mt2 = st.tabs(["Historic ratings", "Season simulations"])
    with mt1:
        sel = st.multiselect(
        f"Team ({len(ratings_by_team_df)} options)",
        teams,
        default = teams[0],
        max_selections = 50,
        key="team_sel")

        if sel:           
            filtered = ratings_df[sel]
                
            fig = plot_multi(filtered)
            st.pyplot(fig,width='stretch')
            plt.close(fig)
    with mt2:
        season_dates = get_seasons_daterange(scores_csv)

        season_league_teams = get_seasons_tiers_teams(scores_csv)

        season_list = season_league_teams.index.get_level_values("Season").unique().tolist()

        sel_season = st.selectbox(
        "Choose season",
        season_list,
        index = len(season_list)-1,
        key="sel_season")

        selected = season_league_teams.loc[sel_season]
        tier_divisions = selected.index.tolist()

        sel_league = st.selectbox(
        "Choose league",
        tier_divisions,
        index = None,
        key="league_sel")

        if sel_league:
            sel_teams = season_league_teams.loc[ (sel_season,*sel_league) ]

            pre_season_date = season_dates.loc[sel_season]["pre"]
            for team in sel_teams:
                st.write(team, ratings_by_team_df.loc[team][pre_season_date])




    
