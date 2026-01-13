import pandas as pd
import numpy as np
from typing import NamedTuple


class AssetTimeSeries(NamedTuple):
    # both fields contain one column per asset, with time index
    prices: pd.DataFrame # historical prices
    log_returns: pd.DataFrame # historical log returns


class AssetMetrics(NamedTuple):
    daily_return: pd.Series # one value per asset
    daily_vol: pd.Series # same shape
    annual_return: pd.Series # same shape
    annual_vol: pd.Series # same shape


class AssetRiskProfile(NamedTuple):
    time_series: AssetTimeSeries
    metrics: AssetMetrics


class PortofolioTimeSeries(NamedTuple):
    prices: pd.Series # 



class PortfolioRiskReturn(NamedTuple):
    daily_return: int | float
    daily_vol: int | float
    annual_return: int | float
    annual_vol: int | float


def get_asset_risk_return(
        dfs: list[pd.DataFrame], 
        asset_names: list[str], 
        price_field_name: str
):
    '''
    given a dictionary of asset name to its DataFrame, extract specified
    price field name from each DataFrame and construct a new one, with 
    asset name as the price colume name. 

    The caller is responsible for aligning data with asset names

    :param df_map: Description
    :type df_map: dict[str, pd.DataFrame]
    :param price_field_name: Description
    :type price_field_name: str
    '''

    if len(dfs) != len(asset_names):
        raise ValueError(f'{len(dfs)} DataFrames vs {len(asset_names)} names')
    
    prices = pd.concat([df[price_field_name] for df in dfs], axis=1)
    prices.columns = asset_names
    
    log_returns = np.log(prices / prices.shift(1)).iloc[1:]

    daily_return = log_returns.mean()
    daily_vol = log_returns.std()

    annual_return = daily_return * 252 # business day count in a year
    annual_vol = daily_vol * np.sqrt(252)
    
    return AssetRiskReturn(
        prices=prices,
        log_returns=log_returns,
        daily_return=daily_return,
        daily_vol=daily_vol,
        annual_return=annual_return,
        annual_vol=annual_vol,
    )


def get_portfolio_risk_return(
        asset_risk_return: AssetRiskReturn, 
        weights: np.ndarray
) -> PortfolioRiskReturn:
    '''
    Given individual asset risk/return profile, and weights for each asset,
    this function computes the portfolio level risk/return profile
    
    The portfolio characteristics are described in a MATLAB style language:
    Let normalized weights be a column vector w;
    Let covariance matrix of the lognormally (in theory) distributted ∑
    
    If daily return across different assets are r as a column vector,
    then the daily return of the portfolio is r_p = w * r (linear combination)

    Then the variance is Var(r_p) = Var(w * r) = w' * ∑ * w 
    by variance of a linear combination

    :param asset_risk_return: Description
    :type asset_risk_return: AssetRiskReturn
    :param weights: Description
    :type weights: np.ndarray
    :return: Description
    :rtype: AssetRiskReturn
    '''
    normalized_weights = weights / np.sum(weights)

    

