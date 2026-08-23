import csv
import pandas as pd
import streamlit as st
from collections import defaultdict
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
    live_ratings["home_adv"] = 150
    home_success = []
    home_winex = []
    home_res_hash = { "H": 1, "D": 0.5, "A": 0}
    
    with open(scores_csv, newline="") as f:
        reader = csv.DictReader(f)
        #Date,Season,HomeTeam,AwayTeam,Score,hGoal,aGoal,Division,Tier,Result

        current_season = None
    
                
        for row in reader:
            date = row["Date"]
            season = row["Season"]

            if current_season is None:
                current_season = season
                
            if current_season != season:
                if len(home_success) > 2000:
                    print(len(home_success))
                    # update home adv and save end of season ratings
                    # save...
                    print(f"\n{current_season}")
                    av_home_success = round(sum(home_success[-2000:])/len(home_success[-2000:]),5)
                    av_home_winex = round( sum(home_winex[-2000:])/len(home_winex[-2000:]),5)
                    print("Average home success vs win ex:",av_home_success, av_home_winex)
                    print("Corresponding diffs", w_to_diff[int(100000*av_home_success)], w_to_diff[int(100000*av_home_winex)])
                    print("Current home advantage:", live_ratings["home_adv"])
                    discr = w_to_diff[int(100000*av_home_success)] - w_to_diff[int(100000*av_home_winex)]
                    live_ratings["home_adv"] = np.round(discr,0).astype(int) + live_ratings["home_adv"]
                    print("New home adv: ", live_ratings["home_adv"])
                current_season = season

                            
            home_team = row["HomeTeam"]
            away_team = row["AwayTeam"]
            home_score = int(row["hGoal"])
            away_score = int(row["aGoal"])

            rating_home_new, rating_away_new, win_ex_home = get_new_ratings(live_ratings, home_team, away_team, home_score, away_score)
            rating_history.append( { "date": date,  "season": season, "team": home_team, "rating": rating_home_new} )
            rating_history.append( { "date": date, "season": season, "team": away_team, "rating": rating_away_new} )
            live_ratings[home_team] = rating_home_new
            live_ratings[away_team] = rating_away_new 

            home_success.append( home_res_hash[row["Result"]] )
            home_winex.append(win_ex_home)

    return teams, rating_history, home_success, home_winex
