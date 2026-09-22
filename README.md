# interrogating-the-pyramid

See: https://interrogating-the-pyramid.streamlit.app/

## What is this?

Macro-level stats, visualisations and attempted predictions for the top 4 tiers of the English football pyramid using an ELO-style ratings model

**Data used:** English top 4 tiers results from https://github.com/seanelvidge/England-football-results

## What is the rating model? 

Given a match between a home team with rating $R_H$ and an away team with match $R_A$, the home team win expectancy is calculated via:

$W_H = \frac{1}{1 + 10^{-d/400}}$ with $d = R_H - R_A + \Delta_H$

where $\Delta_H$ is a home advantage factor. The away team win expectancy is $W_A = 1 - W_H$.
For each team, the new rating is 

$R_{\text{new}} = R + K \cdot G \cdot ( O - W)$

where the outcome $O$ is 1 for a win, $0.5$ for a draw and $0$ for a loss; $K$ is a constant which determines how many points are involved in the update, and $G$ is a function of the goal difference of the result.

**Current model:** $K =20$, $G$ follows www.eloratings.net, where $G = 1$ if a draw or one-goal victory, $G=1.5$ for a two-goal victory, and $G= 1.75 + (g-3)/8$ for a victory by $g \geq 3$ goals. Teams start with an initial rating of 1500.

Teams start with a rating of 1500, and the home advantage $\Delta_H$ is initially set to 150.

### What happens with home advantage?
Over time the discrepancy between the average actual home outcomes and the average home win expectancy can be used to update $\Delta_H$.
I do this as follows:

1) wait until a sufficient amount $N$ of match results have been recorded (e.g. $N=1000$ or $N=2000$)
2) then at set intervals (the start of new seasons), I compute the average over the last $N$ results of the home win expectancies and the actual home outcome. From these averages I calculate associated putative rating differences which I decompose into a part intrinsic to the "actual" strength of the teams and a part which comes from home advantage, writing $d\_{\text{expected}} = d_{\text{teams}} + \Delta_H$, $d\_{\text{actual}}  = d_{\text{teams}} + (\Delta_H)\_\text{actual}$. Then the model home advantage can be updated to:

   $$\Delta_H \rightarrow  (\Delta_H)\_\text{actual} =  d\_{\text{actual}}  - d\_{\text{expected}} + \Delta_H $$

For sensible choices of $N$ and the intervals at which to update, this leads to a rolling average home win expectancy which tracks that observed in actual results.

## What statistics can I look at?

**Ratings over time**

**Graphs of relationships and trends (collective and team-wise)** for statistics such as ratings, rating changes, match results, goals for/against...

**Leage tables at any date** (n.b. excluding point deductions at the moment)

## What can be simulated?

Any league season from any start date. Using Monte Carlo simulations in which I generate the scorelines of each match via Poisson distributions chosen to reproduce the Elo win expectancy as explained here https://github.com/blaircda/world-cup-sim/blob/main/Elo_to_Poisson.md

## What else can be predicted?

Predicted may be over-selling it, but I display some (non-interactive) results for time series regression on collective (tier-wise) home win proportion, and individual Premier League 2026/2027 teams' win, draw and goal for/against proportion.
