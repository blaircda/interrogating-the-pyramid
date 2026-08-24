import csv
import pandas as pd
import streamlit as st
from collections import defaultdict
from rating_model import *
from config import *

@st.cache_data
def build_ratings(teams_csv, scores_csv):
    # import all teams separately
    teams = []
    
    with open(teams_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams.append(row["Team"])    

    # live ratings - continually updated while calculating ratings
    live_ratings = {team:default_rating for team in teams}
    live_ratings["home_adv"] = initial_home_adv

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
    update_home_adv_counter = 0
    when_update_home_adv = 100   

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

            # check if we have reached a new season
            if season != current_season:

                # save the end of season ratings and model home advantage
                snapshot = { "season_end": current_season, "season_start": season } | live_ratings
                season_ratings.append( snapshot ) 

                # update the model home advantage
                # using previous N matches 
                if len(home_success) > N:
                    # update home adv and save end of season ratings
                    #print(f"\n{current_season}")
                    av_home_success = round(sum(home_success[-N:])/N,5)
                    av_home_winex = round( sum(home_winex[-N:])/N,5)
                    #print("Average home success vs win ex:",av_home_success, av_home_winex)
                    #print("Corresponding diffs", w_to_diff[int(100000*av_home_success)], w_to_diff[int(100000*av_home_winex)])
                    #print("Current home advantage:", live_ratings["home_adv"])
                    discr = w_to_diff[int(100000*av_home_success)] - w_to_diff[int(100000*av_home_winex)]
                    live_ratings["home_adv"] += np.round(discr,0).astype(int)
                    #print("New home adv: ", live_ratings["home_adv"])

                # set current_season to the nwe season
                current_season = season

            # alternatively update home_adv every X matches
            if len(home_success) > N and update_home_adv_counter == when_update_home_adv:
                    pass
                    av_home_success = round(sum(home_success[-N:])/N,5)
                    av_home_winex = round( sum(home_winex[-N:])/N,5)
                    discr = w_to_diff[int(100000*av_home_success)] - w_to_diff[int(100000*av_home_winex)]
                    live_ratings["home_adv"] += np.round(discr,0).astype(int)
                    update_home_adv_counter = 0 

            # match details
            home_team = row["HomeTeam"]
            away_team = row["AwayTeam"]
            home_score = int(row["hGoal"])
            away_score = int(row["aGoal"])

            # get new ratings for the teams involved
            rating_home_new, rating_away_new, win_ex_home = get_new_ratings(live_ratings, home_team, away_team, home_score, away_score)
            rating_history.append( { "date": date,  "season": season, "team": home_team, "rating": rating_home_new} )
            rating_history.append( { "date": date, "season": season, "team": away_team, "rating": rating_away_new} )
            # update live rating 
            live_ratings[home_team] = rating_home_new
            live_ratings[away_team] = rating_away_new 
            # record the actual home result and its predicted win expectancy
            home_success.append( home_res_hash[row["Result"]] )
            home_winex.append(win_ex_home)

            update_home_adv_counter += 1
            
    return teams, rating_history, season_ratings, home_success, home_winex
