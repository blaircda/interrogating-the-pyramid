import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from config import *
from import_process import (
    process_data,
    get_ratings_at_date
)
from plotting import (
    plot_multi_ratings, plot_multi_cols,
    plot_model_home_adv, plot_model_home_adv_compare,
    )
from helpers import (
    multiselect_teams, filter_by_season_and_teams,
    select_season_range
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

st.set_page_config(layout="wide", page_title="Ratings | Interrogating the pyramid")
# control width of content display 
#padl, content, padr = st.columns([0.1,0.8,0.1])

#with content:

st.header("Ratings")
st.write("Based on an ELO-style model")

ratings_tab, home_adv_tab = st.tabs(["Ratings", "Model home advantage"])

with ratings_tab:
    st.subheader("Team ratings")
    s1, s2 = select_season_range(season_list, "ratings")
    sel_teams = multiselect_teams(teams, "ratings")
    filtered_ratings = filter_by_season_and_teams(ratings_df, s1, s2, sel_teams)
    fig = plot_multi_ratings(filtered_ratings, sel_teams)
    st.pyplot(fig,width="content")
    plt.close(fig)


########################################################################
# tab: Home Advantage
########################################################################
with home_adv_tab:
########################################################################
#  Historical Home Advantage
########################################################################
    st.subheader("Historic home advantage")
    st.write("This shows average home wins as a proportion of all results, and average home success for which a win counts as 1 and a draw as 0.5")
    # season range slider
    s1, s2 = st.select_slider(
        "Season range",
        options = season_list,
        value = (start_season, end_season),
        key = "homeadv_season_slider"
        )

    filtered = home_adv[ ( s1 <= home_adv.index) & (home_adv.index <= s2)]
    fig = plot_multi_cols(
            filtered,
            ["AvHomeSuccess", "AvHomeWins"],
            {"AvHomeSuccess": "Av. Home Success", "AvHomeWins": "Av. Home Wins"}
            )
    st.pyplot(fig)
    plt.close(fig)
########################################################################
# Model Home Advantage
########################################################################
    st.subheader("Model home advantage")
    st.write(f"Starting from initial home advantage {initial_home_adv} rating points")
    st.write(f"Updating model home advantage at start of every season based on previous {N_matches_home_adv} matches")

    # plot model home advantage over time
    fig = plot_model_home_adv( season_ratings_end.xs("home_adv", level=1) )
    st.pyplot(fig)
    plt.close(fig)
    # plot comparison between model home win ex and actual home success
    fig = plot_model_home_adv_compare(av_discr, 20)
    st.pyplot(fig)
    plt.close(fig)
