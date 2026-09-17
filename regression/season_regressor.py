import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.feature_selection import RFECV
from sklearn.feature_selection import SelectKBest, f_regression

########################################################################
# helper functions
########################################################################

def drop_incomplete_seasons(df, seasons):
    df = df.drop(seasons, level="Season")
    return df

def make_lags(df, cols, lags):
    lagged = pd.concat(
        {
            f"{c}_{lag}": df[c].shift(lag)
            for lag in lags
            for c in cols
        },
        axis=1,
    )
    df = pd.concat([df, lagged], axis=1)
    return df

def make_rolling_avs(df, cols, windows):
    rolled = pd.concat(
        {
            f"{c}_Av{w}": df[c].rolling(window=w).mean().shift(1) 
            for w in windows
            for c in cols
        },
        axis=1,
    )
    df = pd.concat([df, rolled], axis=1)
    return df
            
def get_season_means( df, cols = None ):
    df = df.copy()
    if cols is None:
        cols = df.columns
    df = df.groupby("Season")[cols].mean()
    df["NSeason"] = np.arange(len(df.index))
    return df

########################################################################
# ridge regressor
########################################################################

def ridge_regress_with_feature_gridsearch(df, target, df_future, verbose=True):   
    """
    performs ridge regression with a feature/alpha parameter grid search 
    with X = df[all cols except target], y = df[target]
    predicts on df_future

    return prediction, a plot, and information about the fit
    """
    # make features
    X = df.copy()
    X.drop(target,axis=1, inplace=True)
    X.dropna(inplace=True) 

    # make target
    y = df.loc[:, target]  
    # align on dropped na values
    y, X = y.align(X, join='inner') 
    
    # make pipeline
    ridge_pipeline = Pipeline([
        ('scaler', StandardScaler()), 
        ('selector', SelectKBest(score_func=f_regression)),          
        ('ridge', Ridge())  
    ])

    # grid search params
    param_grid = {
        'selector__k': [1,2,3, 'all'], 
        'ridge__alpha': [0.001, 0.01, 0.05, 0.1, 0.5, 1.0],
    }

    # time series split
    tscv = TimeSeriesSplit(n_splits=5)
    
    #  grid search
    grid_search = GridSearchCV(
        estimator=ridge_pipeline,
        param_grid=param_grid,
        cv=tscv,
        scoring='neg_mean_absolute_error',
        return_train_score=True
    )
    
    grid_search.fit(X, y)
    Xfuture = df_future.drop(target, axis=1)
    future_pred = grid_search.predict(Xfuture)

    # extract details about the best fit 
    best_pipeline = grid_search.best_estimator_
    best_selector = best_pipeline.named_steps['selector']
    feature_mask = best_selector.get_support()
    selected_feature_names = np.array(X.columns)[feature_mask]

    best_params = grid_search.best_params_
    best_score = -grid_search.best_score_

    # details of best model
    best_ridge_model = best_pipeline.named_steps['ridge']
    scaled_weights = best_ridge_model.coef_
    scaled_intercept = best_ridge_model.intercept_
    # undo scaling 
    scaler = best_pipeline.named_steps['scaler']    
    means = scaler.mean_[feature_mask]
    std_devs = scaler.scale_[feature_mask]
    raw_weights = scaled_weights / std_devs
    raw_intercept = scaled_intercept - np.sum((scaled_weights * means) / std_devs)
    equation_terms = [f"{raw_intercept:.4f}"]
    for name, w_raw in zip(selected_feature_names, raw_weights):
        sign = "+" if w_raw >= 0 else "-"
        equation_terms.append(f"{sign} ({abs(w_raw):.4f} * {name})")
    best_forecast =  f"Forecasted {target} = " + " ".join(equation_terms)

    # graph fit against data
    y_pred_array = grid_search.predict(X)
    y_pred = pd.Series(y_pred_array, index=y.index)
    fig, ax = plt.subplots(figsize=(12, 6))
    # Plot actual target
    y.plot(ax=ax, label="Actual Data")
    ax.plot(y_pred, label="Ridge model")
    ax.set_title(f"{target} (Ridge Regression)\n")
    ax.set_ylabel(f"{target}Prop")
    ax.text(
        0.025, -0.125,           
        best_forecast+"\n"+f"Best params: {best_params}"+"\n"+f"Validation score: {best_score:.4f}", 
        transform=ax.transAxes, # position text rel to bounding box 
        fontsize=10, 
        verticalalignment='top',
        horizontalalignment='left',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='gray')
    )
    ax.legend()

    if verbose:        
        print(f"Optimal settings: {best_params}")
        print(f"Top validation score: {best_score:.4f}")
        #print(f"Selected features: {selected_feature_names}")
        print(f"Forecasted {target} = " + " ".join(equation_terms))
        plt.show()
        print("Predictions:")
        Xfuture["predicted_"+target] = future_pred
        print(Xfuture[ list(selected_feature_names)+["predicted_"+target] ].to_string())

    return future_pred, fig, best_forecast, best_params, best_score

########################################################################
# ridge regressor preparatory functions
########################################################################

def regress_seasons( tables, target, base_cols, lag_cols, ave_cols, leaky_cols, future_split):
    """
    tables = df of data
    target = either str or list of strings
    base_cols = list of columns from which to derive features
    lag_cols = list of columns from which to derive lag features
    ave_cols = list of columns from which to derive rolling average features
    leaky_cols = sublist of base_cols to exclude from actual regression
    future_split = index value on which to divide tables into past and future
    """
    # keep only cols in base cols
    # average at season level over all
    df = get_season_means( tables[ base_cols ] )
    # lag/average selected features
    df = make_lags(df,  lag_cols, [1,2])
    df = make_rolling_avs(df, lag_cols, [5,10])

    # force target into list so can write one loop over it
    if not isinstance(target, list):
        target = [target]

    predictions = {}
    figures = {}
    
    for var in target:
        # after lagging remove features which contain future (i.e. end of season) information
        # but do not drop target as that is used in the regression function
        cols_to_drop_set = set(leaky_cols)
        if var in cols_to_drop_set:
            cols_to_drop_set.remove(var) 
        dfX = df.drop(columns=cols_to_drop_set)
        #print("About to regress with possible features:", dfX.columns)
        # split past and future
        df_fut = dfX.loc[[future_split]]
        df_past = dfX.drop(future_split)
        # regress
        pred, fig, eqn, params, score = ridge_regress_with_feature_gridsearch(df_past, var, df_fut, verbose=False)
        predictions[var] = {
            "pred": pred,
            "fig": fig,
            "eqn": eqn,
            "params": params,
            "val_score": score
        }
        
    return predictions
    
def regress_seasons_tier(tier, tables, target, base_cols, lag_cols, ave_cols, leaky_cols, future_split):
    """
    filter tables by tier before passing to regress_seasons
    """
    df = tables.xs(tier, level="Tier")[base_cols]
    return regress_seasons( df,  target, base_cols, lag_cols, ave_cols, leaky_cols, future_split)

def regress_seasons_team( team, tables, target, base_cols, lag_cols, ave_cols, leaky_cols, future_split):
    """
    filter tables by team before passing to regress_seasons
    """
    df = tables.xs(team, level="Team")[base_cols]
    seasons = df.index.get_level_values("Season")
    since_first_season = int(seasons.max()[:4]) - int(seasons.min()[:4])+1
    if (len(df) > since_first_season):
        print("Team has been relegated from top 4 tiers -- missing data")
    elif (len(df) < 10):
        print("Team has been present in top 4 tiers for insufficently long to regress")
    else:   
        return regress_seasons( df,  target, base_cols, lag_cols, ave_cols, leaky_cols, future_split)

