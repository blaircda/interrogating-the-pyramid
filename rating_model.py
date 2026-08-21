import numpy as np

# lookup table for win ex
diff_to_w = [round(1/( 10**(-diff/400)+1),2) for diff in range(-2000,2001)]
# lookup table for goal margin of victory c.f. eloratings.net 
gd_adj = [1,1,1.5,1.75] + [1.75 + (N-3)/8 for N in range(4,51)]

def get_new_ratings(ratings, home_team, away_team, home_score, away_score):

    home_team_rating = ratings[home_team]
    away_team_rating = ratings[away_team]

    margin = abs(home_score - away_score)
    K = 20
    G = gd_adj(margin) 
        
    home_adv = 50
    rating_diff = home_team_rating - away_team_rating + home_adv
    
    win_ex1 = diff_to_w[rating_diff+2000]
    win_ex2 = 1 - win_ex1
    
    if home_score > away_score:
        Delta = round(K*G*win_ex2,0)
    elif home_score < away_score: # team2 wins
        Delta = -round(K*G*win_ex1,0)
    else: # draw
        Delta = round(K*(0.5-win_ex1),0)

    home_team_rating = home_team_rating + int(Delta)
    away_team_rating = away_team_rating - int(Delta)

    return home_team_rating, away_team_rating
