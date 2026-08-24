# interrogating-the-pyramid
English football historic result data analysis
(work in progress)

See: https://interrogating-the-pyramid.streamlit.app/

Data: sourced from https://github.com/seanelvidge/England-football-results

## Some unnecessary backgound

When I was a child I found a fascinating book in my grandparents' attic, where you could generate football league seasons by rolling dice to produce scores, using a pencil to fill in a grid of the results before calculating by hand the surprises of the final table. Luckily my uncles had grown bored of this exercise halfway through, so I was able to finish the book (being an Irish child in the late 1990s, I cheated in favour of Manchester United). With the book dating from, presumably, the 70s, the teams were not all the teams I was familiar with. This was perhaps my introduction to the strange historical depths of the intangible cultural heritage that is the English football pyramid. (I suspect my enjoyment of this structure shares something with my enjoyment of novels with maps and appendices.)

## The idea

Refine and backtest ELO-style club rating system (still in progress)

## ELO structure

Given a match between a home team with rating $R_H$ and an away team with match $R_A$, the home team win expectancy is calculated via:
$xW_H = \frac{1}{1 + 10^{-d/400}} \qquad d = R_H - R_A + H$
where $H$ is a home advantage factor. The away team win expectancy is $W_A = 1 - W_H$.
The new ratings are
$R' = R + K \cdot G \cdot ( O - xW)$
where the outcome $O$ is 1 for a win, $0.5$ for a draw and $0$ for a loss; $K$ is a constant which determines how many points are involved in the update, and $G$ is a function of the goal difference of the result.

Teams start with a rating of 1500, and the home advantage $H$ is initially set to 150.
Over time the discrepancy between the average actual home outcomes and the average home win expectancy can be used to update $H$.

