"""
Example demonstrating trade sequence backtesting functionality.

This example shows various ways to create and backtest arbitrary trade sequences
using the new trade list functionality in cwrubacktest.
"""

import pandas as pd
import pytz
from datetime import datetime, timedelta

# Import the new trade sequence functionality
from cwrubacktest.trading_strats.trade import Trade, TradeList
from cwrubacktest.trading_strats.trade_utils import (
    create_simple_trades,
    create_dollar_cost_averaging_trades, 
    create_momentum_trades,
    merge_trade_lists
)
from cwrubacktest.backtest.trade_sequence import create_trade_sequence_backtest
from cwrubacktest.alpha_models.trade_list import TradeListAlphaModel
from cwrubacktest.asset.equity import Equity
from cwrubacktest.asset.universe.static import StaticUniverse
from cwrubacktest.data_handler.data_handler import BacktestDataHandler
from cwrubacktest.data_handler.csv_handler import CSVDailyBarDataSource
from cwrubacktest.statistics.tearsheet import TearsheetStatistics


def example_1_simple_trade_sequence():
    """Example 1: Simple sequence of individual trades."""
    
    print("=== Example 1: Simple Trade Sequence ===")
    
    # Create individual trades manually
    trades = [
        Trade(
            timestamp=pd.Timestamp('2025-02-15 09:30:00', tz=pytz.UTC),
            asset='EQ:SPY',
            action='BUY',
            value=50000  # Buy $50k worth of SPY
        ),
        Trade(
            timestamp=pd.Timestamp('2025-02-20 09:30:00', tz=pytz.UTC),
            asset='EQ:TLT',
            action='BUY',
            value=30000  # Buy $30k worth of TLT
        ),
        Trade(
            timestamp=pd.Timestamp('2025-03-01 09:30:00', tz=pytz.UTC),
            asset='EQ:SPY',
            action='SELL',
            value=25000  # Sell $25k worth of SPY
        ),
        Trade(
            timestamp=pd.Timestamp('2025-03-10 09:30:00', tz=pytz.UTC),
            asset='EQ:TLT',
            action='SELL',
            value=30000  # Sell all TLT
        )
    ]
    
    # Create trade list
    trade_list = TradeList(trades)
    
    # Set up data handler for market data
    csv_dir = "/home/rikome/Public/cwrubacktest/"  # Adjust path as needed
    data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=['SPY', 'TLT'])
    
    # Create backtest
    backtest = create_trade_sequence_backtest(
        trades=trade_list,
        initial_cash=100000,
        data_handler=BacktestDataHandler(
            StaticUniverse(['EQ:SPY', 'EQ:TLT']),
            data_sources=[data_source]
        ),
        rebalance_frequency='on_trade_dates'
    )
    
    # Validate and run
    validation = backtest.validate_trades()
    print(f"Validation: {validation}")
    
    if validation['valid']:
        print("Running backtest...")
        backtest.run()
        
        # Get results
        execution_summary = backtest.get_trade_execution_summary()
        print(f"Execution Summary: {execution_summary}")
        
        # Show trade preview
        trade_preview = backtest.preview_trades()
        print("\nTrade Preview:")
        print(trade_preview)
        
        return backtest
    else:
        print("Validation failed:", validation['issues'])
        return None


def example_2_dollar_cost_averaging():
    """Example 2: Dollar cost averaging strategy."""
    
    print("\n=== Example 2: Dollar Cost Averaging ===")
    
    # Create DCA trades for SPY
    dca_trades = create_dollar_cost_averaging_trades(
        asset='EQ:SPY',
        start_date='2025-02-01',
        end_date='2025-03-15',
        investment_amount=5000,  # $5k per month
        frequency='monthly'
    )
    
    print(f"Created {len(dca_trades)} DCA trades")
    print("DCA Trade Schedule:")
    print(dca_trades.to_dataframe())
    
    # Set up data handler
    csv_dir = "/home/rikome/Public/cwrubacktest/"
    data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=['SPY'])
    
    # Create and run backtest
    backtest = create_trade_sequence_backtest(
        trades=dca_trades,
        initial_cash=50000,
        data_handler=BacktestDataHandler(
            StaticUniverse(['EQ:SPY']),
            data_sources=[data_source]
        )
    )
    
    backtest.run()
    return backtest


def example_3_momentum_strategy():
    """Example 3: Simple momentum strategy with signals."""
    
    print("\n=== Example 3: Momentum Strategy ===")
    
    # Create momentum signals (simplified example)
    signal_dates = ['2025-02-15', '2025-02-20', '2025-02-25', '2025-03-01', '2025-03-05', '2025-03-10']
    signals = [0.8, 0.6, -0.3, -0.7, 0.2, 0.9]  # Momentum signals
    
    momentum_trades = create_momentum_trades(
        asset='EQ:SPY',
        signal_dates=signal_dates,
        signals=signals,
        position_size=20000,  # $20k position size
        threshold=0.5  # Signal threshold
    )
    
    print(f"Created {len(momentum_trades)} momentum trades")
    print("Momentum Trades:")
    print(momentum_trades.to_dataframe())
    
    # Set up and run backtest
    csv_dir = "/home/rikome/Public/cwrubacktest/"
    data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=['SPY'])
    
    backtest = create_trade_sequence_backtest(
        trades=momentum_trades,
        initial_cash=100000,
        data_handler=BacktestDataHandler(
            StaticUniverse(['EQ:SPY']),
            data_sources=[data_source]
        )
    )
    
    backtest.run()
    return backtest


def example_4_combined_strategies():
    """Example 4: Combining multiple trade strategies."""
    
    print("\n=== Example 4: Combined Strategies ===")
    
    # Create different trade strategies
    spy_dca = create_dollar_cost_averaging_trades(
        asset='EQ:SPY',
        start_date='2025-02-01', 
        end_date='2025-03-15',
        investment_amount=3000,
        frequency='monthly'
    )
    
    tlt_trades = create_simple_trades(
        asset='EQ:TLT',
        dates=['2025-02-18', '2025-03-05'],
        actions=['BUY', 'SELL'],
        values=[15000, 15000]
    )
    
    # Merge strategies
    combined_trades = merge_trade_lists(spy_dca, tlt_trades)
    
    print(f"Combined strategy has {len(combined_trades)} total trades")
    print("Combined Trade Schedule:")
    print(combined_trades.to_dataframe().sort_values('timestamp'))
    
    # Run backtest
    csv_dir = "/home/rikome/Public/cwrubacktest/"
    data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=['SPY', 'TLT'])
    
    backtest = create_trade_sequence_backtest(
        trades=combined_trades,
        initial_cash=100000,
        data_handler=BacktestDataHandler(
            StaticUniverse(['EQ:SPY', 'EQ:TLT']),
            data_sources=[data_source]
        )
    )
    
    backtest.run()
    return backtest


def example_5_csv_trades():
    """Example 5: Loading trades from CSV file."""
    
    print("\n=== Example 5: CSV Trade Loading ===")
    
    # Create a sample CSV file
    csv_data = {
        'timestamp': ['2025-02-15', '2025-02-20', '2025-02-25', '2025-03-01'],
        'asset': ['EQ:SPY', 'EQ:TLT', 'EQ:SPY', 'EQ:TLT'],
        'action': ['BUY', 'BUY', 'SELL', 'SELL'],
        'value': [25000, 15000, 10000, 15000]
    }
    
    df = pd.DataFrame(csv_data)
    csv_path = '/tmp/sample_trades.csv'
    df.to_csv(csv_path, index=False)
    
    # Load trades from CSV
    csv_trades = TradeList.from_csv(csv_path)
    
    print(f"Loaded {len(csv_trades)} trades from CSV")
    print("CSV Trades:")
    print(csv_trades.to_dataframe())
    
    # Run backtest
    csv_dir = "/home/rikome/Public/cwrubacktest/"
    data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=['SPY', 'TLT'])
    
    backtest = create_trade_sequence_backtest(
        trades=csv_trades,
        initial_cash=100000,
        data_handler=BacktestDataHandler(
            StaticUniverse(['EQ:SPY', 'EQ:TLT']),
            data_sources=[data_source]
        )
    )
    
    backtest.run()
    return backtest


def compare_strategies(backtests, strategy_names):
    """Compare multiple backtesting strategies."""
    
    print("\n=== Strategy Comparison ===")
    
    equity_curves = []
    for i, backtest in enumerate(backtests):
        if backtest is not None:
            equity_curve = backtest.get_equity_curve()
            equity_curve.columns = [strategy_names[i]]
            equity_curves.append(equity_curve)
    
    if equity_curves:
        # Combine equity curves
        combined_df = pd.concat(equity_curves, axis=1)
        print("Final Portfolio Values:")
        print(combined_df.tail(1))
        
        # Calculate returns
        returns = combined_df.pct_change().dropna()
        print("\nStrategy Statistics:")
        for strategy in returns.columns:
            total_return = (combined_df[strategy].iloc[-1] / combined_df[strategy].iloc[0] - 1) * 100
            volatility = returns[strategy].std() * (252**0.5) * 100  # Annualized
            sharpe = returns[strategy].mean() / returns[strategy].std() * (252**0.5) if returns[strategy].std() > 0 else 0
            
            print(f"{strategy}:")
            print(f"  Total Return: {total_return:.2f}%")
            print(f"  Volatility: {volatility:.2f}%")
            print(f"  Sharpe Ratio: {sharpe:.2f}")


if __name__ == "__main__":
    print("Trade Sequence Backtesting Examples")
    print("==================================")
    
    # Run examples
    backtests = []
    strategy_names = []
    
    try:
        # Example 1: Simple trades
        bt1 = example_1_simple_trade_sequence()
        backtests.append(bt1)
        strategy_names.append("Simple Trades")
        
        # Example 2: Dollar cost averaging
        bt2 = example_2_dollar_cost_averaging()
        backtests.append(bt2)
        strategy_names.append("DCA Strategy")
        
        # Example 3: Momentum strategy
        bt3 = example_3_momentum_strategy()
        backtests.append(bt3)
        strategy_names.append("Momentum Strategy")
        
        # Example 4: Combined strategies
        bt4 = example_4_combined_strategies()
        backtests.append(bt4)
        strategy_names.append("Combined Strategy")
        
        # Example 5: CSV trades
        bt5 = example_5_csv_trades()
        backtests.append(bt5)
        strategy_names.append("CSV Strategy")
        
        # Compare all strategies
        compare_strategies(backtests, strategy_names)
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have the required data files (SPY.csv, TLT.csv) in the correct directory.")
