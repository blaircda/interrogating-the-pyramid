import csv
import pandas as pd
import streamlit as st
from rating_model import *

@st.cache_data
def build_ratings(teams_csv, scores_csv):
    ratings = {}
    teams = []

    with open(teams_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams.append(row["Team"])

    with open(scores_csv, newline="") as f:
        reader = csv.DictReader(f)
        #seen_teams = set()
        last_date_read = None
        for row in reader:
            date = row["Date"]

            home_team = row["HomeTeam"]
            away_team = row["AwayTeam"]
            home_score = int(row["hGoal"])
            away_score = int(row["aGoal"])
            
            #print(f"Match on {date}")
            if date not in ratings:
                # we have ticked over to a new date
                # copy the previous ratings over to the new date
                # and then alter them 
                ratings[date] = ratings.get(last_date_read,{}).copy()

            #if home_team not in seen_teams:
            #    seen_teams.add(home_team)
            #if away_team not in seen_teams:
            #    seen_teams.add(away_team)          

            r = ratings[date]
            r[home_team], r[away_team] = get_new_ratings(r, home_team, away_team, home_score, away_score)
            last_date_read = date

    ratings_by_team = {}

    for team in teams:
        ratings_by_team[team] = {}
        for date in ratings.keys():
            ratings_by_team[team][date] = ratings[date].get(team, None)

    return teams, ratings, ratings_by_team
