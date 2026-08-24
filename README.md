# interrogating-the-pyramid
English football historic result data analysis/simulation
(work in progress)

See: https://interrogating-the-pyramid.streamlit.app/

Data: sourced from https://github.com/seanelvidge/England-football-results

## Some unnecessary background

When I was a child I found a fascinating book in my grandparents' attic, where you could generate football league seasons by rolling dice to produce scores, using a pencil to fill in a grid of the results before calculating by hand the surprises of the final table. Luckily my uncles had grown bored of this exercise halfway through, so I was able to finish the book (being an Irish child in the late 1990s, I cheated in favour of Manchester United). I forget if this was just for the top division or for the full league system - either way with the book being a couple of decades old, many of the teams appearing were unfamiliar and mysterious to me. This was perhaps my introduction to the strange historical depths of the intangible cultural heritage that is the English football pyramid. (I suspect my enjoyment of this structure shares something with my enjoyment of novels with maps and appendices.)

## The idea

Construct an ELO rating system from first principles, test it on any season of the English football top 4 divisions, apply it to current and future seasons

## ELO structure

Given a match between a home team with rating $R_H$ and an away team with match $R_A$, the home team win expectancy is calculated via:

$W_H = \frac{1}{1 + 10^{-d/400}}$ with $d = R_H - R_A + \Delta_H$

where $\Delta_H$ is a home advantage factor. The away team win expectancy is $W_A = 1 - W_H$.
For each team, the new rating is 

$R_{\text{new}} = R + K \cdot G \cdot ( O - W)$

where the outcome $O$ is 1 for a win, $0.5$ for a draw and $0$ for a loss; $K$ is a constant which determines how many points are involved in the update, and $G$ is a function of the goal difference of the result.

The constant $K$ is currently 20, and the goal difference factor $G$ used is that of eloratings.net, where $G = 1$ if a draw or one-goal victory, $G=1.5$ for a two-goal victory, and $G= 1.75 + (g-3)/8$ for a victory by $g \geq 3$ goals.

Teams start with a rating of 1500, and the home advantage $\Delta_H$ is initially set to 150.
Over time the discrepancy between the average actual home outcomes and the average home win expectancy can be used to update $\Delta_H$.
I do this as follows:

1) wait until a sufficient amount $N$ of match results have been recorded (e.g. $N=1000$ or $N=2000$)
2) then at set intervals (the start of new seasons), I compute the average over the last $N$ results of the home win expectancies and the actual home outcome. From these averages I calculate associated putative rating difference $d\_{\text{expected}} = d_{\text{teams}} + \Delta_H$, and the latter as corresponding to a putative rating difference $d\_{\text{actual}}  = d_{\text{teams}} + (\Delta_H)\_\text{actual}$. Then the actual home advantage can be updated to:

   $$\Delta_H \rightarrow  (\Delta_H)\_\text{actual} =  d\_{\text{actual}}  - d\_{\text{expected}} + \Delta_H $$

For sensible choices of $N$ and the intervals at which to update, this leads to a rolling average home win expectancy which tracks that observed in actual results.

## Season simulation model

For each league, the teams are assigned the ratings calculated using the above method up till the end of the previous season.
Then I generate the scorelines of each match via Poisson distributions chosen to reproduce the Elo win expectancy as explained here https://github.com/blaircda/world-cup-sim/blob/main/Elo_to_Poisson.md
