import pandas as pd
import pytz

from cwrubacktest.backtest.backtest import BacktestTradingSession
from cwrubacktest.alpha_models.trade_list import TradeListAlphaModel, TradeSequenceAlphaModel
from cwrubacktest.trading_strats.trade import TradeList, Trade
from cwrubacktest.asset.universe.static import StaticUniverse
from cwrubacktest.trading_strats.rebalance import RebalancePeriod
from cwrubacktest.broker.fee_model.zero_fee_model import ZeroFeeModel


class TradeSequenceBacktest(BacktestTradingSession):
    """
    Specialized backtest class for running backtests based on predefined trade sequences.
    
    This class extends BacktestTradingSession to handle trade lists more efficiently
    and provides additional features specific to trade sequence backtesting.
    
    Parameters
    ----------
    trade_list : `TradeList`
        The sequence of trades to execute.
    initial_cash : `float`, optional
        Starting portfolio value (default: $1,000,000).
    fee_model : `FeeModel`, optional
        Transaction cost model to use.
    data_handler : `DataHandler`, optional
        Data handler for market data (required for value-based trades).
    rebalance_frequency : `str`, optional
        How often to check for trades ('daily', 'on_trade_dates', 'never').
        Default is 'on_trade_dates' which only rebalances on dates with trades.
    **kwargs
        Additional arguments passed to BacktestTradingSession.
    """
    
    def __init__(
        self,
        start_dt,
        end_dt,
        trade_list,
        initial_cash=1e6,
        fee_model=None,
        data_handler=None,
        rebalance_frequency='on_trade_dates',
        **kwargs
    ):
        """
        Initialize a trade sequence backtest.
        
        Parameters
        ----------
        start_dt : `pd.Timestamp`
            The starting datetime (UTC) of the backtest.
        end_dt : `pd.Timestamp`
            The ending datetime (UTC) of the backtest.
        trade_list : `TradeList`
            The list of trades to execute during the backtest.
        initial_cash : `float`, optional
            Starting portfolio value.
        fee_model : `FeeModel`, optional
            Transaction cost model.
        data_handler : `DataHandler`, optional
            Market data handler.
        rebalance_frequency : `str`, optional
            Rebalancing frequency ('daily', 'on_trade_dates', or 'never').
        **kwargs
            Additional arguments passed to BacktestTradingSession.
        """
        if not isinstance(trade_list, TradeList):
            raise ValueError("trade_list must be a TradeList object")
        
        self.trade_list = trade_list
        self.rebalance_frequency = rebalance_frequency
        
        # Validate that trades are within the backtest period
        trade_start, trade_end = trade_list.get_date_range()
        if trade_start is not None and trade_start < start_dt:
            raise ValueError(f"Trade date {trade_start} is before backtest start {start_dt}")
        if trade_end is not None and trade_end > end_dt:
            raise ValueError(f"Trade date {trade_end} is after backtest end {end_dt}")
        
        # Use default fee model if none provided
        if fee_model is None:
            fee_model = ZeroFeeModel()
        
        # Create universe from trade assets
        assets = list(trade_list.get_assets())
        universe = StaticUniverse(assets)
        
        # Create trade-based alpha model
        alpha_model = TradeSequenceAlphaModel(trade_list, data_handler, universe)
        
        # Set rebalance period based on frequency
        if rebalance_frequency == 'daily':
            rebalance_pd = RebalancePeriod.DAILY
        elif rebalance_frequency == 'on_trade_dates':
            rebalance_pd = RebalancePeriod.DAILY  # We'll override the schedule
        elif rebalance_frequency == 'never':
            rebalance_pd = RebalancePeriod.NEVER
        else:
            raise ValueError("rebalance_frequency must be 'daily', 'on_trade_dates', or 'never'")
        
        # Determine portfolio type and parameters
        # Check if we have short trades or need to support selling
        has_short_trades = any(trade.action in ['SHORT', 'COVER'] for trade in trade_list)
        has_sell_trades = any(trade.action in ['SELL'] for trade in trade_list)
        
        if has_short_trades or has_sell_trades:
            # If we have short trades or sell trades, we need a long/short portfolio
            portfolio_long_only = False
            if 'gross_leverage' not in kwargs:
                kwargs['gross_leverage'] = 1.0  # Default leverage
        else:
            # If only long trades, use long-only portfolio
            portfolio_long_only = True
            if 'cash_buffer_percentage' not in kwargs:
                kwargs['cash_buffer_percentage'] = 0.05  # Default 5% cash buffer
        
        # Initialize parent class
        super().__init__(
            start_dt=start_dt,
            end_dt=end_dt,
            universe=universe,
            alpha_model=alpha_model,
            initial_cash=initial_cash,
            rebalance_pd=rebalance_pd,
            long_only=portfolio_long_only,
            fee_model=fee_model,
            data_handler=data_handler,
            **kwargs
        )
        
        # Override rebalance schedule if using trade dates only
        if rebalance_frequency == 'on_trade_dates':
            self.rebalance_schedule = self._create_trade_date_rebalance_schedule()
    
    def _create_trade_date_rebalance_schedule(self):
        """
        Create a rebalance schedule that only includes dates with trades.
        
        Returns
        -------
        list[pd.Timestamp]
            List of rebalance timestamps corresponding to trade dates.
        """
        trade_dates = self.alpha_model.get_trade_dates()
        
        # Filter trade dates to be within simulation period
        valid_dates = []
        for date in trade_dates:
            if self.start_dt.date() <= date.date() <= self.end_dt.date():
                # Convert to market close time (21:00:00 UTC) for consistency with backtest timing
                trade_timestamp = pd.Timestamp(f"{date.date()} 21:00:00", tz=pytz.UTC)
                valid_dates.append(trade_timestamp)
        
        return sorted(valid_dates)
    
    def get_trade_execution_summary(self):
        """
        Get a summary of trade execution during the backtest.
        
        Returns
        -------
        dict
            Summary statistics about trade execution.
        """
        progress = self.alpha_model.get_sequence_progress()
        
        return {
            'total_trades': progress['total'],
            'executed_trades': progress['executed'],
            'execution_rate': progress['percentage'],
            'is_complete': self.alpha_model.is_sequence_complete(),
            'trade_date_range': self.trade_list.get_date_range(),
            'backtest_date_range': (self.start_dt, self.end_dt)
        }
    
    def get_unexecuted_trades(self):
        """
        Get trades that were not executed during the backtest.
        
        Returns
        -------
        list[Trade]
            List of trades that were not executed.
        """
        unexecuted = []
        for trade in self.trade_list:
            trade_id = id(trade)
            if trade_id not in self.alpha_model.executed_trades:
                unexecuted.append(trade)
        return unexecuted
    
    def preview_trades(self):
        """
        Preview all trades in the sequence.
        
        Returns
        -------
        pd.DataFrame
            DataFrame showing all trades with execution status.
        """
        df = self.alpha_model.preview_trades()
        
        # Add execution status
        execution_status = []
        for _, row in df.iterrows():
            # Find the corresponding trade object
            trade = None
            for t in self.trade_list:
                if (t.timestamp == row['timestamp'] and 
                    t.asset == row['asset'] and 
                    t.action == row['action']):
                    trade = t
                    break
            
            if trade is not None:
                trade_id = id(trade)
                status = 'Executed' if trade_id in self.alpha_model.executed_trades else 'Pending'
            else:
                status = 'Unknown'
            
            execution_status.append(status)
        
        df['execution_status'] = execution_status
        return df
    
    def validate_trades(self):
        """
        Validate that all trades can be executed with available data.
        
        Returns
        -------
        dict
            Validation results with any issues found.
        """
        issues = []
        warnings = []
        
        # Check date range coverage
        trade_start, trade_end = self.trade_list.get_date_range()
        if trade_start < self.start_dt:
            issues.append(f"Trade start date {trade_start} is before backtest start {self.start_dt}")
        if trade_end > self.end_dt:
            issues.append(f"Trade end date {trade_end} is after backtest end {self.end_dt}")
        
        # Check for value-based trades without data handler
        value_based_trades = [t for t in self.trade_list if t.value is not None]
        if value_based_trades and self.data_handler is None:
            warnings.append(f"Found {len(value_based_trades)} value-based trades but no data handler provided")
        
        # Check for assets in universe
        trade_assets = self.trade_list.get_assets()
        # Use the earliest trade date for universe asset validation
        # If no trades, use a default date
        if self.trade_list:
            validation_date = min(trade.timestamp for trade in self.trade_list)
        else:
            validation_date = pd.Timestamp('2020-01-01', tz=pytz.UTC)
        universe_assets = set(self.universe.get_assets(validation_date))
        missing_assets = trade_assets - universe_assets
        if missing_assets:
            issues.append(f"Assets in trades but not in universe: {missing_assets}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'trade_count': len(self.trade_list),
            'asset_count': len(trade_assets),
            'date_range': (trade_start, trade_end)
        }


def create_trade_sequence_backtest(
    start_dt,
    end_dt,
    trades,
    initial_cash=1e6,
    fee_model=None,
    data_handler=None,
    rebalance_frequency='on_trade_dates',
    **kwargs
):
    """
    Convenience function to create a trade sequence backtest.
    
    Parameters
    ----------
    start_dt : `pd.Timestamp`
        The starting datetime (UTC) of the backtest.
    end_dt : `pd.Timestamp`
        The ending datetime (UTC) of the backtest.
    trades : `TradeList`, `list[Trade]`, `pd.DataFrame`, or `str`
        Trade data in various formats:
        - TradeList object
        - List of Trade objects  
        - DataFrame with trade data
        - Path to CSV file with trade data
    initial_cash : `float`, optional
        Starting portfolio value.
    fee_model : `FeeModel`, optional
        Transaction cost model.
    data_handler : `DataHandler`, optional
        Market data handler.
    rebalance_frequency : `str`, optional
        Rebalancing frequency.
    **kwargs
        Additional arguments for BacktestTradingSession.
        
    Returns
    -------
    TradeSequenceBacktest
        Configured backtest ready to run.
    """
    # Convert input to TradeList
    if isinstance(trades, TradeList):
        trade_list = trades
    elif isinstance(trades, list):
        trade_list = TradeList(trades)
    elif isinstance(trades, pd.DataFrame):
        trade_list = TradeList.from_dataframe(trades)
    elif isinstance(trades, str):
        trade_list = TradeList.from_csv(trades)
    else:
        raise ValueError("trades must be TradeList, list of Trade objects, DataFrame, or CSV path")
    
    # Use default fee model if none provided
    if fee_model is None:
        fee_model = ZeroFeeModel()
    
    return TradeSequenceBacktest(
        start_dt=start_dt,
        end_dt=end_dt,
        trade_list=trade_list,
        initial_cash=initial_cash,
        fee_model=fee_model,
        data_handler=data_handler,
        rebalance_frequency=rebalance_frequency,
        **kwargs
    )
