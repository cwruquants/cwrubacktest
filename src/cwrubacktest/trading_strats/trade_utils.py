"""
Utility functions for creating and manipulating trade sequences.
"""

import pandas as pd
import pytz
from typing import List, Dict, Union
from cwrubacktest.trading_strats.trade import Trade, TradeList


def create_simple_trades(
    asset: str,
    dates: List[str],
    actions: List[str],
    quantities: List[int] = None,
    values: List[float] = None,
    timezone='UTC'
) -> TradeList:
    """
    Create a simple sequence of trades for a single asset.
    
    Parameters
    ----------
    asset : str
        Asset symbol (e.g., 'EQ:SPY').
    dates : list[str]
        List of date strings in YYYY-MM-DD format.
    actions : list[str]
        List of actions ('BUY', 'SELL', 'SHORT', 'COVER').
    quantities : list[int], optional
        List of quantities for each trade.
    values : list[float], optional
        List of dollar values for each trade.
    timezone : str, optional
        Timezone for the timestamps (default: 'UTC').
        
    Returns
    -------
    TradeList
        TradeList containing the specified trades.
    """
    if len(dates) != len(actions):
        raise ValueError("dates and actions must have the same length")
    
    if quantities is not None and len(quantities) != len(dates):
        raise ValueError("quantities must have the same length as dates")
    
    if values is not None and len(values) != len(dates):
        raise ValueError("values must have the same length as dates")
    
    if quantities is None and values is None:
        raise ValueError("Either quantities or values must be provided")
    
    trades = []
    for i, (date_str, action) in enumerate(zip(dates, actions)):
        timestamp = pd.to_datetime(date_str).tz_localize(timezone)
        quantity = quantities[i] if quantities is not None else None
        value = values[i] if values is not None else None
        
        trade = Trade(
            timestamp=timestamp,
            asset=asset,
            action=action,
            quantity=quantity,
            value=value
        )
        trades.append(trade)
    
    return TradeList(trades)


def create_rebalancing_trades(
    assets: List[str],
    rebalance_dates: List[str],
    target_weights: List[Dict[str, float]],
    portfolio_value: float = 100000,
    timezone='UTC'
) -> TradeList:
    """
    Create trades for portfolio rebalancing to target weights.
    
    Parameters
    ----------
    assets : list[str]
        List of asset symbols.
    rebalance_dates : list[str]
        List of rebalancing dates in YYYY-MM-DD format.
    target_weights : list[dict]
        List of target weight dictionaries for each rebalancing date.
        Each dict maps asset symbols to target weights (0.0 to 1.0).
    portfolio_value : float, optional
        Total portfolio value to allocate (default: $100,000).
    timezone : str, optional
        Timezone for timestamps (default: 'UTC').
        
    Returns
    -------
    TradeList
        TradeList containing rebalancing trades.
    """
    if len(rebalance_dates) != len(target_weights):
        raise ValueError("rebalance_dates and target_weights must have same length")
    
    trades = []
    current_weights = {asset: 0.0 for asset in assets}  # Start with no positions
    
    for date_str, target_weight_dict in zip(rebalance_dates, target_weights):
        timestamp = pd.to_datetime(date_str).tz_localize(timezone)
        
        # Validate target weights sum to 1.0
        total_weight = sum(target_weight_dict.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Target weights on {date_str} sum to {total_weight}, must sum to 1.0")
        
        # Calculate position changes needed
        for asset in assets:
            current_weight = current_weights.get(asset, 0.0)
            target_weight = target_weight_dict.get(asset, 0.0)
            weight_change = target_weight - current_weight
            
            if abs(weight_change) > 0.001:  # Only trade if meaningful change
                trade_value = abs(weight_change) * portfolio_value
                action = 'BUY' if weight_change > 0 else 'SELL'
                
                trade = Trade(
                    timestamp=timestamp,
                    asset=asset,
                    action=action,
                    value=trade_value
                )
                trades.append(trade)
            
            # Update current weights
            current_weights[asset] = target_weight
    
    return TradeList(trades)


def create_dollar_cost_averaging_trades(
    asset: str,
    start_date: str,
    end_date: str,
    investment_amount: float,
    frequency='monthly',
    timezone='UTC'
) -> TradeList:
    """
    Create trades for dollar cost averaging strategy.
    
    Parameters
    ----------
    asset : str
        Asset symbol to invest in.
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.
    investment_amount : float
        Dollar amount to invest each period.
    frequency : str, optional
        Investment frequency ('daily', 'weekly', 'monthly', 'quarterly').
    timezone : str, optional
        Timezone for timestamps.
        
    Returns
    -------
    TradeList
        TradeList containing DCA trades.
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Generate date range based on frequency
    if frequency == 'daily':
        dates = pd.bdate_range(start, end, freq='B')  # Business days
    elif frequency == 'weekly':
        dates = pd.date_range(start, end, freq='W-MON')  # Weekly on Mondays
    elif frequency == 'monthly':
        dates = pd.date_range(start, end, freq='MS')  # Month start
    elif frequency == 'quarterly':
        dates = pd.date_range(start, end, freq='QS')  # Quarter start
    else:
        raise ValueError("frequency must be 'daily', 'weekly', 'monthly', or 'quarterly'")
    
    trades = []
    for date in dates:
        timestamp = date.tz_localize(timezone)
        trade = Trade(
            timestamp=timestamp,
            asset=asset,
            action='BUY',
            value=investment_amount
        )
        trades.append(trade)
    
    return TradeList(trades)


def create_momentum_trades(
    asset: str,
    signal_dates: List[str],
    signals: List[float],
    position_size: float = 10000,
    threshold: float = 0.0,
    timezone='UTC'
) -> TradeList:
    """
    Create trades based on momentum signals.
    
    Parameters
    ----------
    asset : str
        Asset symbol to trade.
    signal_dates : list[str]
        List of signal dates in YYYY-MM-DD format.
    signals : list[float]
        List of signal values (positive = bullish, negative = bearish).
    position_size : float, optional
        Dollar amount for each position (default: $10,000).
    threshold : float, optional
        Signal threshold for triggering trades (default: 0.0).
    timezone : str, optional
        Timezone for timestamps.
        
    Returns
    -------
    TradeList
        TradeList containing momentum trades.
    """
    if len(signal_dates) != len(signals):
        raise ValueError("signal_dates and signals must have same length")
    
    trades = []
    current_position = 0  # -1 = short, 0 = flat, 1 = long
    
    for date_str, signal in zip(signal_dates, signals):
        timestamp = pd.to_datetime(date_str).tz_localize(timezone)
        
        # Determine desired position based on signal
        if signal > threshold:
            desired_position = 1  # Long
        elif signal < -threshold:
            desired_position = -1  # Short
        else:
            desired_position = 0  # Flat
        
        # Generate trades if position change needed
        if desired_position != current_position:
            # Close existing position first
            if current_position != 0:
                close_action = 'SELL' if current_position > 0 else 'COVER'
                close_trade = Trade(
                    timestamp=timestamp,
                    asset=asset,
                    action=close_action,
                    value=position_size
                )
                trades.append(close_trade)
            
            # Open new position
            if desired_position != 0:
                open_action = 'BUY' if desired_position > 0 else 'SHORT'
                open_trade = Trade(
                    timestamp=timestamp,
                    asset=asset,
                    action=open_action,
                    value=position_size
                )
                trades.append(open_trade)
            
            current_position = desired_position
    
    return TradeList(trades)


def create_trades_from_csv(
    csv_path: str,
    timestamp_column: str = 'timestamp',
    asset_column: str = 'asset',
    action_column: str = 'action',
    quantity_column: str = 'quantity',
    value_column: str = 'value',
    **kwargs
) -> TradeList:
    """
    Create TradeList from CSV file with flexible column mapping.
    
    Parameters
    ----------
    csv_path : str
        Path to CSV file.
    timestamp_column : str, optional
        Name of timestamp column (default: 'timestamp').
    asset_column : str, optional
        Name of asset column (default: 'asset').
    action_column : str, optional
        Name of action column (default: 'action').
    quantity_column : str, optional
        Name of quantity column (default: 'quantity').
    value_column : str, optional
        Name of value column (default: 'value').
    **kwargs
        Additional arguments passed to pd.read_csv().
        
    Returns
    -------
    TradeList
        TradeList created from CSV data.
    """
    df = pd.read_csv(csv_path, **kwargs)
    
    # Rename columns to standard names
    column_mapping = {
        timestamp_column: 'timestamp',
        asset_column: 'asset',
        action_column: 'action'
    }
    
    if quantity_column in df.columns:
        column_mapping[quantity_column] = 'quantity'
    if value_column in df.columns:
        column_mapping[value_column] = 'value'
    
    df = df.rename(columns=column_mapping)
    
    return TradeList.from_dataframe(df)


def merge_trade_lists(*trade_lists: TradeList) -> TradeList:
    """
    Merge multiple TradeList objects into a single TradeList.
    
    Parameters
    ----------
    *trade_lists : TradeList
        Variable number of TradeList objects to merge.
        
    Returns
    -------
    TradeList
        Merged TradeList containing all trades, sorted by timestamp.
    """
    all_trades = []
    for trade_list in trade_lists:
        all_trades.extend(trade_list.trades)
    
    merged = TradeList(all_trades)
    merged.sort_by_timestamp()
    return merged


def filter_trades_by_asset(trade_list: TradeList, assets: List[str]) -> TradeList:
    """
    Filter trades to only include specified assets.
    
    Parameters
    ----------
    trade_list : TradeList
        Original trade list.
    assets : list[str]
        List of asset symbols to keep.
        
    Returns
    -------
    TradeList
        Filtered TradeList.
    """
    filtered_trades = [trade for trade in trade_list if trade.asset in assets]
    return TradeList(filtered_trades)


def filter_trades_by_date_range(
    trade_list: TradeList,
    start_date: str = None,
    end_date: str = None
) -> TradeList:
    """
    Filter trades to only include those within a date range.
    
    Parameters
    ----------
    trade_list : TradeList
        Original trade list.
    start_date : str, optional
        Start date in YYYY-MM-DD format.
    end_date : str, optional
        End date in YYYY-MM-DD format.
        
    Returns
    -------
    TradeList
        Filtered TradeList.
    """
    filtered_trades = []
    
    start_ts = pd.to_datetime(start_date) if start_date else None
    end_ts = pd.to_datetime(end_date) if end_date else None
    
    for trade in trade_list:
        include = True
        if start_ts and trade.timestamp < start_ts:
            include = False
        if end_ts and trade.timestamp > end_ts:
            include = False
        
        if include:
            filtered_trades.append(trade)
    
    return TradeList(filtered_trades)
