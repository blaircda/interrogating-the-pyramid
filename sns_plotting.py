import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import linregress

# wrappers for basic sns plots

# name and sort ascending for "most" value
stats_positional = {
    "POS": ("Final position", True),
    "Rstart_rank": ("Initial rating rank (league)",True),
    "Rend_rank": ("Final rating rank (league)",True),
    "Rrank_change": ("Change in rating rank (league)",False),
    "POSPyr": ("Position in pyramid",True),
    "RPyr_start": ("Initial rating rank (pyramid)",True),
    "RPyr_end": ("Final rating rank (pyramid)",True),
    "RPyr_change": ("Change in rating rank (pyramid)",False)
}

stats_fundamental = {
    "Rstart": ("Initial rating",False),
    "Rend": ("Final rating",False), 
    "Rchange": ("Change in rating",False),
    "Rbelow_start": ("Initial diff to max rating (league)",True),
    "Rbelow_end": ("Final diff to max rating (league)",True),
    "PTSpg": ("Points per game",False),
    "GFpg": ("Goals for per game",False),
    "GApg": ("Goals against per game",False),
    "Gpg": ("Total goals per game",False),
    "GFHpg": ("Home goals for per game",False),
    "GAHpg": ("Home goals against per game",False),
    "GFApg": ("Away goals for per game",False),
    "GAApg": ("Away goals against per game",False),
    "Wpg": ("Win proportion",False),
    "Dpg": ("Draw proportion",False),
    "Lpg": ("Loss proportion",False),
    "WHpg": ("Home win proportion",False),
    "DHpg": ("Home draw proportion",False),
    "LHpg": ("Home loss proportion",False),
    "WApg": ("Away win proportion",False),
    "DApg": ("Away draw proportion",False),
    "LApg": ("Away loss proportion",False),
}

table_labels = stats_positional | stats_fundamental 

def format_title_scatter(ax, x, y, hue, selection):
    title = ""
    
    if hue is not None:
        title += f"{table_labels.get(y,y)[0]} vs {table_labels.get(x,x)[0]} by {hue}"
    else:
        title += f"{table_labels.get(y,y)[0]} vs {table_labels.get(x,x)[0]}"
    if selection:
        title+=f"\n{selection}"
    ax.set_title(title)

def format_title_seasons(ax, x, y, hue, selection):
    title = ""
    
    if hue is not None:
        title += f"{table_labels.get(y,y)[0]} vs Season by {hue}"
    else:
        title += f"{table_labels.get(y,y)[0]} vs Season"
    if selection:
        title+=f"\n{selection}"
    ax.set_title(title)
    
def format_legend(ax, hue, xpos, ypos):
    if hue is not None:
        ax.legend(
        title = hue,
        loc="upper center",
        bbox_to_anchor=(xpos, ypos),
        ncols=4
        )  

def format_seasons(ax,x,y,seasons):
    """
    format seasons axis
    """
    ax.set_xlabel("Season")
    ax.set_ylabel(table_labels.get(y,y)[0])
    labels = [t.get_text() for t in ax.get_xticklabels()]
    N = max(1, len(seasons) // 10)
    ticks = seasons[::N]
    ax.set_xticks(seasons[::N])
    ax.set_xticklabels(seasons[::N])
    ax.tick_params(axis="x", labelbottom=True, rotation=90)

def format_ax_pos(ax,x,y,df):
    posn_labels = ["POS", "Rstart_rank", "Rend_rank", "POSPyr", "RPyr_start", "RPyr_end"]

    if x in posn_labels:
        max_pos = int(df[x].max())+1
        N = max(1, max_pos // 5)
        posl = list(range(1, max_pos, N))
        ax.set_xlim(max_pos, 0)
        ax.set_xticks(posl) 
    if y in posn_labels:
        max_pos =int(df[y].max())+1
        N = max(1, max_pos // 5)
        posl = list(range(1, max_pos, N))
        ax.set_ylim(max_pos, 0)
        ax.set_yticks(posl) 


def plot_scatter(df, x, y, hue, selection=None):
    
    fig, ax = plt.subplots()
    
    sns.scatterplot(
        data=df,
        x=x,
        y=y,
        hue=hue,
        ax = ax
    )

    ax.grid(True, alpha = 0.3)
    ax.set_xlabel(table_labels.get(x,x)[0])
    ax.set_ylabel(table_labels.get(y,y)[0])

    format_ax_pos(ax,x,y,df)
        
    format_title_scatter(ax, x, y, hue, selection)
    format_legend(ax, hue, 0.5,-0.1)
    return fig

def plot_line(df, x, y, hue, selection=None):
    
    fig, ax = plt.subplots()
    
    sns.lineplot(
        data=df,
        x=x,
        y=y,
        hue=hue,
        ax = ax
    )

    ax.grid(True, alpha = 0.3)
    ax.set_xlabel(table_labels.get(x,x)[0])
    ax.set_ylabel(table_labels.get(y,y)[0])

    format_ax_pos(ax,x,y,df)
            
    format_title(ax, x, y, hue, selection)
    format_legend(ax, hue, 0.5,-0.1)
  
    return fig

def plot_line_all_seasons(df, x, y, hue, style=None, selection=None):

    seasons = (
        df.index.get_level_values("Season")
          .unique()
          .sort_values()
    )
    
    fig, ax = plt.subplots()

    sns.lineplot(
        data=df,
        x=x,
        y=y,
        hue=hue,
        style=style,
        palette="dark",
        estimator="mean",
        errorbar=lambda x: (x.min(), x.max()),
        ax = ax
    )

    ax.grid(True, alpha = 0.3)

    format_seasons(ax,x,y, seasons)
    format_ax_pos(ax,x,y,df)
    format_title_seasons(ax, x, y, hue, selection)
    format_legend(ax, hue, 0.5,-0.3)
    
    return fig


def plot_team_line_all_seasons(df, x, y, hue, style=None, selection=None, annotate_tier =False):

    seasons = (
        df.index.get_level_values("Season")
          .unique()
          .sort_values()
    )
    
    fig, ax = plt.subplots()

    sns.lineplot(
        data=df,
        x=x,
        y=y,
        hue=hue,
        style=style,
        palette="dark",
        estimator="mean",
        errorbar=lambda x: (x.min(), x.max()),
        ax = ax
    )

    ax.grid(True, alpha = 0.3)

    format_seasons(ax,x,y, seasons)
    format_ax_pos(ax,x,y,df)
    format_title_seasons(ax, x, y, hue, selection)
    format_legend(ax, hue, 0.5,-0.3)
    if annotate_tier:
        for team, group in df.groupby(level="Team"):
            tier = group.index.get_level_values("Tier").to_series(index=group.index)
            changed = tier.ne(tier.shift())
            for idx in group.index[changed]:
                season = idx[0]
                tier = idx[1]
                val = group.loc[idx, y]
                ax.axvline(
                        season,
                        color="tomato",
                        linewidth=0.,
                        linestyle="--"
                        )
                ax.annotate(
                    f"T{tier}",
                    (season, val),
                    xytext=(12, 5),
                    ha="center",
                    textcoords="offset points",
                    arrowprops=dict(
                                color='tomato',  # Arrow color
                                width=0.5,  # Shaft width
                                headwidth=3,  # Head width
                                headlength=2,  # Head length
                                linewidth=0.2,            # Thickness of the outline
                                #connectionstyle='arc3,rad=+0.5'
                            ),
                    color="tomato"
                )
        
    return fig

def relplot_line_all_seasons(df, x, y, hue, selection=None):

    seasons = (
        df.index.get_level_values("Season")
          .unique()
          .sort_values()
    )

    g = sns.relplot(
        data=df,
        x=x,
        y=y,
        hue=hue,
        kind="line",
        estimator="mean",
        errorbar=lambda x: (x.min(), x.max()),
        row="Tier",
        height=5,
        aspect=1.5,
    )

    for ax in g.axes.flat:
        ax.grid(True, alpha = 0.3)
        format_seasons(ax, x, y, seasons)
        format_legend(ax, hue, 0.5,-0.3)

      
    g.set_titles(row_template="Tier {row_name}")
    g.figure.suptitle(f"{table_labels.get(y,y)[0]} vs {table_labels.get(x,x)[0]}")
    g.figure.subplots_adjust(hspace=0.225,top=0.95)
    return g
    
def plot_reg(df, x, y, selection=None):
    fig, ax = plt.subplots()
    
    sns.regplot(
        data=df,
        x=x,
        y=y,
        ax = ax
    )

    ax.grid(True, alpha = 0.3)
    ax.set_xlabel(table_labels.get(x,x)[0])
    ax.set_ylabel(table_labels.get(y,y)[0])
    
    if x == "POS":
        ax.set_xlim(df["POS"].max()+1, 0)
        ax.set_xticks([1,5,10,15,20])
    if y == "POS":
        ax.set_ylim(df["POS"].max()+1, 0)
        ax.set_yticks([1,5,10,15,20])

    title = f"Linear regression of {table_labels.get(y,y)[0]} vs {table_labels.get(x,x)[0]}"
    if selection:
        title+=f"\n{selection}"

    ax.set_title(title)

    return fig

def plot_reg_values(df, x, y, selection=None):
    res = linregress(df[x], df[y])

    fig, ax = plt.subplots()
        
    sns.regplot(
        data=df,
        x=x,
        y=y,
        ax = ax
    )

    stats_text = (
        f"Slope: {res.slope:.4f}\n"
        f"Intercept: {res.intercept:.4f}\n"
        f"Std Error: {res.stderr:.4f}\n"
        f"R²: {res.rvalue**2:.4f}"
    )

    ax.text(
        1.05, 0.95,           
        stats_text, 
        transform=ax.transAxes, # position text rel to bounding box 
        fontsize=10, 
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='gray')
    )

    if x == "POS":
        ax.set_xlim(df["POS"].max()+1, 0)
        ax.set_xticks([1,5,10,15,20])
    if y == "POS":
        ax.set_ylim(df["POS"].max()+1, 0)
        ax.set_yticks([1,5,10,15,20])
        
    ax.grid(True, alpha = 0.3)
    ax.set_xlabel(table_labels.get(x,x)[0])
    ax.set_ylabel(table_labels.get(y,y)[0])

    title = f"Linear regression of {table_labels.get(y,y)[0]} vs {table_labels.get(x,x)[0]}"
    if selection:
        title+=f"\n{selection}"

    ax.set_title(title)

    return fig

def plot_heatmap(df):
    df = df.corr()
    fig, ax = plt.subplots()
    sns.heatmap(df, annot=True, ax=ax)
    return fig
