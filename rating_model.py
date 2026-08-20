
# LOOKUP TABLE FOR WIN EX
diff_to_w = [round(1/( 10**(-diff/400)+1),2) for diff in range(-2000,2001)]


def get_new_ratings(ratings, home_team, away_team, home_score, away_score):
    default_elo = 1500

    home_team_rating = ratings.get(home_team, default_elo)
    away_team_rating = ratings.get(away_team, default_elo)

    K = 100
    G = 1
    home_adv = 0 
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
