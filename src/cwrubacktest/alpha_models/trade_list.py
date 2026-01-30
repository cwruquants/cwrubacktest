import pandas as pd
from cwrubacktest.alpha_models.alpha_model import AlphaModel
from cwrubacktest.trading_strats.trade import TradeList, Trade


class TradeListAlphaModel(AlphaModel):
    """
    An AlphaModel that generates signals based on a predefined list of trades.
    
    This model is designed for backtesting specific trade sequences rather than
    algorithmic signal generation. It executes trades exactly as specified in
    the trade list.
    
    Parameters
    ----------
    trade_list : `TradeList`
        The list of trades to execute during the backtest.
    data_handler : `DataHandler`, optional
        An optional DataHandler used to preserve interface across AlphaModels.
    universe : `Universe`, optional
        The Assets universe (will be inferred from trades if not provided).
    """
    
    def __init__(self, trade_list, data_handler=None, universe=None):
        if not isinstance(trade_list, TradeList):
            raise ValueError("trade_list must be a TradeList object")
        
        self.trade_list = trade_list
        self.data_handler = data_handler
        self.universe = universe
        
        # Sort trades by timestamp for efficient lookup
        self.trade_list.sort_by_timestamp()
        
        # Track executed trades to avoid duplicates
        self.executed_trades = set()
        
        # Cache trades by date for faster lookup
        self._trades_by_date = {}
        self._build_date_cache()
    
    def _build_date_cache(self):
        """Build a cache of trades organized by date for faster lookup."""
        for trade in self.trade_list:
            date_key = trade.timestamp.date()
            if date_key not in self._trades_by_date:
                self._trades_by_date[date_key] = []
            self._trades_by_date[date_key].append(trade)
    
    def __call__(self, dt):
        """
        Generate signals based on trades scheduled for the current datetime.
        
        This method looks for trades scheduled for the current date and converts
        them into position target signals that the portfolio construction can use.
        
        Parameters
        ----------
        dt : `pd.Timestamp`
            The current simulation datetime.
            
        Returns
        -------
        `dict{str: float}`
            Dictionary mapping asset symbols to target position changes.
            Positive values indicate buy signals, negative indicate sell signals.
        """
        signals = {}
        current_date = dt.date()
        
        # Get trades for current date
        trades_today = self._trades_by_date.get(current_date, [])
        
        for trade in trades_today:
            # Skip if trade already executed (prevent duplicates)
            trade_id = id(trade)
            if trade_id in self.executed_trades:
                continue
            
            # Mark trade as executed
            self.executed_trades.add(trade_id)
            
            # Convert trade to signal
            signal = self._trade_to_signal(trade, dt)
            if signal is not None:
                asset = trade.asset
                if asset in signals:
                    # Aggregate multiple trades for same asset on same day
                    signals[asset] += signal
                else:
                    signals[asset] = signal
        
        return signals
    
    def _trade_to_signal(self, trade, dt):
        """
        Convert a Trade object to a signal value.
        
        Parameters
        ----------
        trade : `Trade`
            The trade to convert.
        dt : `pd.Timestamp`
            Current simulation datetime.
            
        Returns
        -------
        float or None
            Signal value for the trade, or None if trade cannot be processed.
        """
        try:
            if trade.quantity is not None:
                # Quantity-based trade
                return trade.to_order_quantity()
            elif trade.value is not None:
                # Value-based trade - need current price to determine quantity
                if self.data_handler is not None:
                    try:
                        # Get current market price
                        price_data = self.data_handler.get_latest_asset_price(dt, trade.asset)
                        if price_data is not None:
                            current_price = trade.price or price_data
                            quantity = int(trade.value / current_price)
                            if trade.is_buy_action:
                                return quantity
                            else:
                                return -quantity
                    except Exception as e:
                        print(f"Warning: Could not get price for {trade.asset} at {dt}: {e}")
                
                # Fallback: return value as signal (portfolio construction will handle conversion)
                if trade.is_buy_action:
                    return trade.value
                else:
                    return -trade.value
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not process trade {trade} at {dt}: {e}")
            return None
    
    def get_trade_dates(self):
        """
        Get all dates that have scheduled trades.
        
        Returns
        -------
        list[pd.Timestamp]
            List of dates with scheduled trades.
        """
        return [pd.Timestamp(date) for date in self._trades_by_date.keys()]
    
    def get_assets(self):
        """
        Get all assets involved in the trade list.
        
        Returns
        -------
        set
            Set of asset symbols.
        """
        return self.trade_list.get_assets()
    
    def preview_trades(self, start_date=None, end_date=None):
        """
        Preview trades in a date range.
        
        Parameters
        ----------
        start_date : `pd.Timestamp`, optional
            Start date for preview (default: all trades).
        end_date : `pd.Timestamp`, optional
            End date for preview (default: all trades).
            
        Returns
        -------
        pd.DataFrame
            DataFrame of trades in the specified range.
        """
        df = self.trade_list.to_dataframe()
        
        if start_date is not None:
            df = df[df['timestamp'] >= start_date]
        if end_date is not None:
            df = df[df['timestamp'] <= end_date]
            
        return df.sort_values('timestamp')
    
    def reset(self):
        """Reset the alpha model to allow re-running the same trade sequence."""
        self.executed_trades.clear()


class TradeSequenceAlphaModel(TradeListAlphaModel):
    """
    Convenience alias for TradeListAlphaModel with additional sequence-oriented methods.
    
    This class adds methods specifically for working with ordered trade sequences
    and provides utilities for common sequence operations.
    """
    
    def __init__(self, trade_list, data_handler=None, universe=None):
        super().__init__(trade_list, data_handler, universe)
        self.sequence_position = 0
    
    def get_next_trade(self):
        """
        Get the next unexecuted trade in the sequence.
        
        Returns
        -------
        Trade or None
            The next trade to execute, or None if sequence is complete.
        """
        for trade in self.trade_list.trades[self.sequence_position:]:
            trade_id = id(trade)
            if trade_id not in self.executed_trades:
                return trade
        return None
    
    def get_sequence_progress(self):
        """
        Get progress through the trade sequence.
        
        Returns
        -------
        dict
            Dictionary with 'executed', 'total', and 'percentage' keys.
        """
        total_trades = len(self.trade_list)
        executed_trades = len(self.executed_trades)
        
        return {
            'executed': executed_trades,
            'total': total_trades,
            'percentage': (executed_trades / total_trades * 100) if total_trades > 0 else 0
        }
    
    def is_sequence_complete(self):
        """
        Check if all trades in the sequence have been executed.
        
        Returns
        -------
        bool
            True if all trades have been executed.
        """
        return len(self.executed_trades) == len(self.trade_list)
