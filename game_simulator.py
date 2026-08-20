import numpy as np

def play_game(team1, team2, state, model_fn):
    """
    returns goals only
    """
    return model_fn(team1, team2, state)
    
########################################################################
# ELO models
########################################################################

# LOOKUP TABLE FOR WIN EX
diff_to_w = [round(1/( 10**(-diff/400)+1),2) for diff in range(-2000,2001)]

# LOOKUP TABLE FOR lams
win_ex_lams = {0.5: (1.4, 1.4),
 0.51: (1.4, 1.36),
 0.52: (1.4, 1.31),
 0.53: (1.4, 1.27),
 0.54: (1.4, 1.23),
 0.55: (1.4, 1.19),
 0.56: (1.4, 1.15),
 0.57: (1.4, 1.1),
 0.58: (1.4, 1.06),
 0.59: (1.4, 1.02),
 0.6: (1.4, 0.99),
 0.61: (1.4, 0.95),
 0.62: (1.4, 0.91),
 0.63: (1.4, 0.87),
 0.64: (1.4, 0.83),
 0.65: (1.4, 0.79),
 0.66: (1.4, 0.76),
 0.67: (1.4, 0.72),
 0.68: (1.4, 0.68),
 0.69: (1.4, 0.65),
 0.7: (1.4, 0.61),
 0.71: (1.4, 0.58),
 0.72: (1.4, 0.54),
 0.73: (1.4, 0.5),
 0.74: (1.4, 0.47),
 0.75: (1.4, 0.43),
 0.76: (1.6, 0.52),
 0.77: (1.6, 0.49),
 0.78: (1.6, 0.45),
 0.79: (1.6, 0.41),
 0.8: (1.8, 0.49),
 0.81: (1.8, 0.45),
 0.82: (1.8, 0.41),
 0.83: (2.0, 0.48),
 0.84: (2.0, 0.43),
 0.85: (2.2, 0.49),
 0.86: (2.2, 0.44),
 0.87: (2.4, 0.49),
 0.88: (2.4, 0.44),
 0.89: (2.6, 0.48),
 0.9: (2.6, 0.42),
 0.91: (2.6, 0.36),
 0.92: (2.8, 0.38),
 0.93: (2.8, 0.31),
 0.94: (3.0, 0.31),
 0.95: (3.2, 0.3),
 0.96: (3.2, 0.21),
 0.97: (3.6, 0.23),
 0.98: (4.0, 0.2),
 0.99: (4.8, 0.21),
 1.0: (6.8, 0.22)
}

def elo_to_poisson(team1, team2, state):
    """
    model function to simulate elo predicted result using Poisson distributions
    """
    home_adv = 0
    diff = state["ratings"][team1] - state["ratings"][team2] + home_adv
    wex = diff_to_w[diff+2000]
    if wex < 0.5:
        wex = round(1 - wex, 2)
    lam1, lam2 = win_ex_lams[wex]
    if(diff>0): # team1 is better
        return  np.random.poisson(lam1), np.random.poisson(lam2)
    else: # team2 is better
        return np.random.poisson(lam2), np.random.poisson(lam1)
