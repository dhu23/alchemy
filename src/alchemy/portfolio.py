import pandas as pd
import numpy as np
from typing import NamedTuple


# Note that all the following 3 data types are equally applicable to portfolio
# level analytics, with just 1-column. This trades purity for uniformity in 
# research code. 
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


def get_asset_risk_profile(
        dfs: list[pd.DataFrame], 
        asset_names: list[str], 
        price_field_name: str
) -> AssetRiskProfile:
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
    
    return AssetRiskProfile(
        time_series=AssetTimeSeries(
            prices=prices,
            log_returns=log_returns,
        ),
        metrics=AssetMetrics(
            daily_return=daily_return,
            daily_vol=daily_vol,
            annual_return=annual_return,
            annual_vol=annual_vol,
        ),
    )


def get_portfolio_risk_profile(
        prices: pd.DataFrame,
        asset_shares: np.ndarray,
) -> AssetRiskProfile:
    '''
    Given asset level time series data, construct portfolio with shares/size of
    For this constructed portfolio, calculated observed risk profile

    :param prices: daily time series DataFrame for each asset
    :type prices: pd.DataFrame
    :param asset_shares: shares/sizes for each asset
    :type asset_shares: np.ndarray
    :return: Description
    :rtype: AssetRiskProfile
    
    '''
    
    if len(prices.columns) != len(asset_shares):
        raise ValueError(
            f'{len(prices.columns)} assets vs {len(asset_shares)} asset shares'
        )
    portfolio_prices = (prices @ asset_shares).to_frame('portfolio')
    portfolio_log_returns = (portfolio_prices / portfolio_prices.shift(1)).dropna()

    daily_return = portfolio_log_returns.mean()
    daily_vol = portfolio_log_returns.std()

    annual_return = daily_return * 252
    annual_vol = daily_vol * np.sqrt(252)

    return AssetRiskProfile(
        time_series=AssetTimeSeries(
            prices=portfolio_prices,
            log_returns=portfolio_log_returns,
        ),
        metrics=AssetMetrics(
            daily_return=daily_return,
            daily_vol=daily_vol,
            annual_return=annual_return,
            annual_vol=annual_vol,
        ),
    )


def get_portfolio_metrics(
        log_returns: pd.DataFrame,
        weights: np.ndarray,
) -> AssetMetrics:
    '''
    
    
    :param log_returns: Description
    :type log_returns: pd.DataFrame
    :param weights: Description
    :type weights: np.ndarray
    :return: Description
    :rtype: AssetMetrics
    '''
    pass


def get_portfolio_risk_profile(
        asset_risk_profile: AssetRiskProfile, 
        weights: np.ndarray,
     
) -> AssetRiskProfile:
    '''
    Given individual asset risk/return profile, and weights for each asset,
    this function computes the portfolio level risk/return profile
    
    The portfolio characteristics are described in a MATLAB style language:
    Let normalized weights be a column vector w (expected input)
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
    (asset_prices, asset_log_returns), asset_metrics = asset_risk_profile
    
    # input weights are expected to be normalized
    portfolio_prices = weights @ asset_prices
    portfolio_log_returns = weights @ asset_log_returns

    # 
    portfolio_daily_returns = weights @ asset_metrics.daily_return
    portfolio_daily_variance = weights @ asset_time_series.log_returns.cov() @ weights
