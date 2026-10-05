import numpy as np

# lookup tables for ratings diff <-> win_expectancy
diff_to_w = [round(1/( 10**(-diff/400)+1),2) for diff in range(-2000,2001)]
w_to_diff = [ -400*np.log10( (1-W/100000)/(W/100000) ) for W in range(1,100000)]
    
# lookup table for goal margin of victory c.f. eloratings.net
gd_adj = [1,1,1.5,1.75] + [1.75 + (N-3)/8 for N in range(4,50)]
# the highest margin of victory in the database is 13
# higher margins may occur in simulations!
#gd_adj = [1, 1, 1.5, 1.75, 1.875, 2.0, 2.125, 2.25, 2.375, 2.5, 2.625, 2.75, 2.875, 3.0]

def get_new_ratings(ratings, home_team, away_team, home_score, away_score):
    """
    computes new ratings for home_team and away_team
    based on their initial ratings stored in dict ratings
    and the result home_score, away_score
    """
    home_team_rating = ratings[home_team]
    away_team_rating = ratings[away_team]

    margin = abs(home_score - away_score)
    K = 20
    G = gd_adj[margin]
        
    home_adv = ratings["home_adv"]
    rating_diff = home_team_rating - away_team_rating + home_adv

    win_ex1 = diff_to_w[rating_diff+2000]

    if home_score > away_score:
        outcome1 = 1
    elif home_score < away_score: # team2 wins
        outcome1 = 0
    else: # draw
        outcome1 = 0.5

    Delta = K*G*(outcome1 - win_ex1)
    home_team_rating += int(Delta)
    away_team_rating -= int(Delta)

    return home_team_rating, away_team_rating, win_ex1
