import csv
import pandas as pd
import streamlit as st
from plotting import *
from import_process import *
from groupings import *
from monte_carlo_simulator import *
from season_simulator import *
from game_simulator import *

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

teams, ratings = build_ratings(teams_csv, scores_csv)

ratings_df = pd.DataFrame.from_dict(ratings)
ratings_df = ratings_df.set_index('date')       
ratings_df.index = pd.to_datetime(ratings_df.index)

st.set_page_config(layout="wide", page_title="Interrogating the pyramid")
col1, col2, col3 = st.columns([0.1,0.8,0.1])

with col2:
    mt1, mt2 = st.tabs(["Historic ratings", "Season simulations"])
    with mt1:
        sel = st.multiselect(
        f"Team ({len(teams)} options)",
        teams,
        default = teams[0],
        max_selections = 50,
        key="team_sel")

        if sel:           
            filtered = ratings_df[ratings_df["team"].isin(sel)]
            fig = plot_multi(filtered, sel)
            st.pyplot(fig,width='stretch')
            plt.close(fig)
            
    with mt2:
        season_dates = get_seasons_daterange(scores_csv)

        season_league_teams = get_seasons_tiers_teams(scores_csv)

        season_list = season_league_teams.index.get_level_values("Season").unique().tolist()

        sel_season = st.selectbox(
        "Choose season",
        season_list[1:],
        index = len(season_list)-2,
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
            
            #if ratings_df.index.is_monotonic_increasing:
            #    st.write("YES")
                
            filtered = ratings_df[ratings_df["team"].isin(sel_teams)  & (ratings_df.index <= pre_season_date)]

            sel_preseason_ratings = {}
            new_teams = []
            for team in sel_teams:
                filtered_team = filtered[ filtered["team"] == team ]
                if not filtered_team.empty:
                    sel_preseason_ratings[team] = int(filtered[(filtered["team"]==team)].iloc[-1]["rating"])
                else:
                    new_teams.append(team)

            if new_teams:
                av_rating = round(sum(sel_preseason_ratings.values())/len(sel_preseason_ratings),0)
                for team in new_teams:
                    sel_preseason_ratings[team] = int(av_rating)
                    #sel_preseason_ratings[team] = 1500

            #st.write(sel_preseason_ratings) 

            state = {
            "teams": sel_teams,
            "ratings": sel_preseason_ratings,
            }

            model_set = {
                    "elo_static": elo_to_poisson,
            }

            Nsims_options = [1,10,100,1000,10000]
            simulate = st.selectbox("Simulate", Nsims_options, index=None, key = "simulater")

            if simulate: 
                simulated_season = run_simulations(state, simulate, model_set, fixtures=None)
                display_results(simulated_season, sel_teams, simulate)


    
