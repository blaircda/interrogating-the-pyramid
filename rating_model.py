import numpy as np

# lookup table for win ex
diff_to_w = [round(1/( 10**(-diff/400)+1),2) for diff in range(-2000,2001)]

w_to_diff = [ -400*np.log10( (1-W/100000)/(W/100000) ) for W in range(1,100000)]

#def w_to_diff(w):
#    """
#    find d corresponding to w
#    """
#    if w >= 0.5:
#        return diff_to_w.index(w)-2000
#    else:
#        return diff_to_w.index(w)
    
# lookup table for goal margin of victory c.f. eloratings.net
#gd_adj = [1,1,1.5,1.75] + [1.75 + (N-3)/8 for N in range(4,14)]
# the highest margin of victory in the database is 13
gd_adj = [1, 1, 1.5, 1.75, 1.875, 2.0, 2.125, 2.25, 2.375, 2.5, 2.625, 2.75, 2.875, 3.0]

def get_new_ratings(ratings, home_team, away_team, home_score, away_score):

    home_team_rating = ratings[home_team]
    away_team_rating = ratings[away_team]

    margin = abs(home_score - away_score)
    K = 20
    G = gd_adj[margin]
        
    home_adv = ratings["home_adv"]
    rating_diff = home_team_rating - away_team_rating + home_adv

    #print(home_team, away_team, rating_diff)
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

    return home_team_rating, away_team_rating, win_ex1
