import csv
import pandas as pd
import streamlit as st
from rating_model import *

@st.cache_data
def build_ratings(teams_csv, scores_csv):
    teams = []
    rating_history = []
    
    default_rating = 1500

    
    with open(teams_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams.append(row["Team"])

    live_ratings = {team:default_rating for team in teams} 

    with open(scores_csv, newline="") as f:
        reader = csv.DictReader(f)
        last_date_read = None
        for row in reader:
            date = row["Date"]

            home_team = row["HomeTeam"]
            away_team = row["AwayTeam"]
            home_score = int(row["hGoal"])
            away_score = int(row["aGoal"])

            rating_home_new, rating_away_new = get_new_ratings(live_ratings, home_team, away_team, home_score, away_score)
            rating_history.append( { "date": date, "team": home_team, "rating": rating_home_new } )
            rating_history.append( { "date": date, "team": away_team, "rating": rating_away_new } )
            live_ratings[home_team] = rating_home_new
            live_ratings[away_team] = rating_away_new 

    return teams, rating_history
