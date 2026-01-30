"""
Simple demonstration of trade sequence backtesting.

This example shows how to create and backtest a simple sequence of trades
using the new trade list functionality.
"""

import sys
sys.path.append("/home/rikome/Public/cwrubacktest/src/")

import pandas as pd
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Import trade sequence functionality

from cwrubacktest.trading_strats.trade import Trade, TradeList
from cwrubacktest.trading_strats.trade_utils import create_simple_trades
from cwrubacktest.backtest.trade_sequence import create_trade_sequence_backtest
from cwrubacktest.asset.equity import Equity
from cwrubacktest.asset.universe.static import StaticUniverse
from cwrubacktest.data_handler.data_handler import BacktestDataHandler
from cwrubacktest.data_handler.csv_handler import CSVDailyBarDataSource


def plot_equity_curve(equity_curve, title="Equity Curve", data_handler=None, initial_cash=100000):
    """Plot the equity curve with trade markers and underlying asset performance."""
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(18, 10))
    
    # Plot equity curve
    equity_curve.index = pd.to_datetime(equity_curve.index)
    ax.plot(equity_curve.index, equity_curve['Equity'], 
            linewidth=3, color='blue', label='Portfolio Value', zorder=3)
    
    # Plot underlying assets for comparison if data handler is provided
    if data_handler is not None:
        print("Attempting to plot underlying asset performance...")
        try:
            # Use the historical closes method which is more reliable
            start_date = equity_curve.index[0]
            end_date = equity_curve.index[-1]
            
            print(f"Getting historical data from {start_date.date()} to {end_date.date()}...")
            
            # Get historical closes for both assets
            price_data = data_handler.get_assets_historical_range_close_price(
                start_date, end_date, ['EQ:SPY', 'EQ:TLT']
            )
            
            if price_data is not None and not price_data.empty:
                print(f"Retrieved price data with shape: {price_data.shape}")
                print(f"Columns: {price_data.columns.tolist()}")
                print(f"Date range: {price_data.index[0].date()} to {price_data.index[-1].date()}")
                
                # Ensure timezone compatibility before reindexing
                if price_data.index.tz is not None and equity_curve.index.tz is None:
                    # Price data is tz-aware, equity curve is tz-naive
                    equity_curve.index = pd.to_datetime(equity_curve.index).tz_localize('UTC')
                elif price_data.index.tz is None and equity_curve.index.tz is not None:
                    # Price data is tz-naive, equity curve is tz-aware
                    price_data.index = pd.to_datetime(price_data.index).tz_localize('UTC')
                
                # Align data with equity curve dates
                aligned_prices = price_data.reindex(equity_curve.index, method='ffill')
                
                if 'EQ:SPY' in aligned_prices.columns and 'EQ:TLT' in aligned_prices.columns:
                    spy_prices = aligned_prices['EQ:SPY'].dropna()
                    tlt_prices = aligned_prices['EQ:TLT'].dropna()
                    
                    if len(spy_prices) > 0 and len(tlt_prices) > 0:
                        # Normalize to initial portfolio value for comparison
                        spy_initial = spy_prices.iloc[0]
                        tlt_initial = tlt_prices.iloc[0]
                        
                        print(f"Initial prices: SPY=${spy_initial:.2f}, TLT=${tlt_initial:.2f}")
                        
                        # Calculate normalized performance (as if investing initial_cash in each asset)
                        spy_normalized = (spy_prices / spy_initial) * initial_cash
                        tlt_normalized = (tlt_prices / tlt_initial) * initial_cash
                        
                        # Plot underlying assets
                        ax.plot(spy_normalized.index, spy_normalized.values, linewidth=2, color='red', 
                               label='SPY (normalized)', alpha=0.7, linestyle='--')
                        ax.plot(tlt_normalized.index, tlt_normalized.values, linewidth=2, color='green', 
                               label='TLT (normalized)', alpha=0.7, linestyle='--')
                        
                        print("Successfully plotted SPY and TLT performance!")
                        
                        # Calculate and display performance comparison
                        spy_return = (spy_normalized.iloc[-1] / initial_cash - 1) * 100
                        tlt_return = (tlt_normalized.iloc[-1] / initial_cash - 1) * 100
                        portfolio_return = (equity_curve['Equity'].iloc[-1] / initial_cash - 1) * 100
                        
                        # Add performance text box
                        performance_text = f"""Performance Comparison:
Portfolio: {portfolio_return:.2f}%
SPY: {spy_return:.2f}%
TLT: {tlt_return:.2f}%"""
                        
                        ax.text(0.02, 0.98, performance_text, transform=ax.transAxes, 
                               verticalalignment='top', bbox=dict(boxstyle='round', 
                               facecolor='wheat', alpha=0.8), fontsize=10)
                    else:
                        print("No valid asset prices found after alignment")
                else:
                    print(f"Required columns not found. Available: {aligned_prices.columns.tolist()}")
            else:
                print("No historical price data returned")
        
        except Exception as e:
            print(f"Note: Could not plot underlying assets: {e}")
            import traceback
            traceback.print_exc()
    
    # Format the plot
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=45)
    
    # Format y-axis with dollar signs
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Add some styling
    plt.tight_layout()
    
    # Show the plot
    plt.show()
    print("Chart displayed above!")
    if data_handler is not None:
        print("Blue line = Your portfolio | Red dashed = SPY | Green dashed = TLT")
    else:
        print("Blue line = Your portfolio (underlying asset data not available)")
    print()


def simple_trade_sequence_demo():
    """Demonstrate basic trade sequence backtesting."""
    
    print("Simple Trade Sequence Demo")
    print("=" * 30)
    
    # Method 1: Create trades manually
    # Note: Use date-only timestamps for daily data compatibility
    trades = [
        Trade(
            timestamp=pd.Timestamp('2025-02-11', tz=pytz.UTC),
            asset='EQ:SPY',
            action='SELL',
            value=70000  # Short 70k worth of SPY
        )
    ]
    
    trade_list = TradeList(trades)
    
    print(f"Created {len(trade_list)} trades:")
    print(trade_list.to_dataframe())
    print()
    
    # Set up data source (using existing CSV files)
    csv_dir = "/home/rikome/Public/cwrubacktest/"
    data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=['SPY', 'TLT'])
    data_handler = BacktestDataHandler(
        StaticUniverse(['EQ:SPY', 'EQ:TLT']),
        data_sources=[data_source]
    )
    
    # Define backtest period - use full data range for comprehensive testing
    start_date = pd.Timestamp('2025-02-11', tz=pytz.UTC)
    end_date = pd.Timestamp('2025-03-13', tz=pytz.UTC)
    
    print(f"Backtest period: {start_date.date()} to {end_date.date()}")
    print()
    
    # Create and configure backtest
    backtest = create_trade_sequence_backtest(
        start_dt=start_date,
        end_dt=end_date,
        trades=trade_list,
        initial_cash=100000,  # Start with $100k
        data_handler=data_handler,
        rebalance_frequency='on_trade_dates'  # Only rebalance on trade dates
    )
    
    # Validate trades before runninga
    validation = backtest.validate_trades()
    print("Trade Validation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Trade count: {validation['trade_count']}")
    print(f"  Asset count: {validation['asset_count']}")
    print(f"  Date range: {validation['date_range']}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")
    if validation['issues']:
        print(f"  Issues: {validation['issues']}")
    print()
    
    # Run the backtest
    if validation['valid']:
        print("Running backtest...")
        backtest.run()
        
        # Get execution summary
        summary = backtest.get_trade_execution_summary()
        print("Execution Summary:")
        print(f"  Total trades: {summary['total_trades']}")
        print(f"  Executed trades: {summary['executed_trades']}")
        print(f"  Execution rate: {summary['execution_rate']:.1f}%")
        print(f"  Sequence complete: {summary['is_complete']}")
        print()
        
        # Show equity curve
        equity_curve = backtest.get_equity_curve()
        print("Equity Curve:")
        print(equity_curve)
        print()
        
        # Calculate simple performance metrics
        initial_value = equity_curve.iloc[0]['Equity']
        final_value = equity_curve.iloc[-1]['Equity']
        total_return = (final_value / initial_value - 1) * 100
        
        print("Performance:")
        print(f"  Initial value: ${initial_value:,.2f}")
        print(f"  Final value: ${final_value:,.2f}")
        print(f"  Total return: {total_return:.2f}%")
        print()
        
        # Plot equity curve with asset comparison
        plot_equity_curve(equity_curve, "Trade Sequence Backtest Results", 
                         data_handler=data_handler, initial_cash=100000)
        
        # Show unexecuted trades (if any)
        unexecuted = backtest.get_unexecuted_trades()
        if unexecuted:
            print(f"\nUnexecuted trades ({len(unexecuted)}):")
            for trade in unexecuted:
                print(f"  {trade.timestamp.date()}: {trade.action} {trade.asset}")
        
        return backtest
    else:
        print("Cannot run backtest due to validation errors.")
        return None


def utility_function_demo():
    """Demonstrate utility functions for creating trades."""
    
    print("\nUtility Function Demo")
    print("=" * 20)
    
    # Create simple trades using utility function
    simple_trades = create_simple_trades(
        asset='EQ:SPY',
        dates=['2025-02-11'],
        actions=['SELL'],
        values=[25000]
    )
    
    print("Trades created with utility function:")
    print(simple_trades.to_dataframe())
    print()
    
    # Show trade list operations
    print("Trade List Operations:")
    assets = simple_trades.get_assets()
    print(f"  Assets involved: {assets}")
    
    date_range = simple_trades.get_date_range()
    print(f"  Date range: {date_range[0].date()} to {date_range[1].date()}")
    
    # Filter trades for specific date
    trades_on_date = simple_trades.get_trades_for_date(pd.Timestamp('2025-02-25'))
    print(f"  Trades on 2025-02-25: {len(trades_on_date)}")


if __name__ == "__main__":
    try:
        # Run the demonstration
        backtest = simple_trade_sequence_demo()
        # utility_function_demo()
        
        print("\nDemo completed successfully!")
        print("\nTo create your own trade sequences:")
        print("1. Create Trade objects with timestamp, asset, action, and quantity/value")
        print("2. Add them to a TradeList")
        print("3. Use create_trade_sequence_backtest() to run the backtest")
        print("4. Or use utility functions like create_simple_trades() for common patterns")
        
    except Exception as e:
        print(f"Error running demo: {e}")
        print("\nMake sure you have:")
        print("1. SPY.csv and TLT.csv files in the current directory")
        print("2. All required dependencies installed")
        print("3. The cwrubacktest package properly installed")
