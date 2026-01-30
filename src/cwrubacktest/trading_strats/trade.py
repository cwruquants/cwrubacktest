import pandas as pd
from dataclasses import dataclass
from typing import Union, Optional


@dataclass
class Trade:
    """
    Represents a single trade in a trade sequence.
    
    Parameters
    ----------
    timestamp : `pd.Timestamp`
        The date-time when the trade should be executed.
    asset : `str`
        The asset symbol to trade (e.g., 'EQ:SPY', 'EQ:AAPL').
    action : `str`
        The trade action: 'BUY', 'SELL', 'SHORT', 'COVER'.
    quantity : `int`, optional
        The number of shares/units to trade. If None, will use value-based sizing.
    value : `float`, optional
        The dollar amount to trade. If None, will use quantity-based sizing.
    price : `float`, optional
        The specific price to use for the trade. If None, will use market price.
    commission : `float`, optional
        Commission override for this specific trade.
    order_id : `str`, optional
        Custom order identifier.
    
    Notes
    -----
    Either quantity or value must be specified, but not both.
    """
    timestamp: pd.Timestamp
    asset: str
    action: str
    quantity: Optional[int] = None
    value: Optional[float] = None
    price: Optional[float] = None
    commission: Optional[float] = None
    order_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate trade parameters after initialization."""
        # Validate action
        valid_actions = {'BUY', 'SELL', 'SHORT', 'COVER'}
        if self.action.upper() not in valid_actions:
            raise ValueError(f"Action must be one of {valid_actions}, got {self.action}")
        
        self.action = self.action.upper()
        
        # Validate that either quantity or value is specified
        if self.quantity is None and self.value is None:
            raise ValueError("Either quantity or value must be specified")
        
        if self.quantity is not None and self.value is not None:
            raise ValueError("Cannot specify both quantity and value")
        
        # Validate numeric values
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.value is not None and self.value <= 0:
            raise ValueError("Value must be positive")
        
        if self.price is not None and self.price <= 0:
            raise ValueError("Price must be positive")
    
    @property
    def is_buy_action(self) -> bool:
        """Returns True if this is a buy action (BUY or COVER)."""
        return self.action in ['BUY', 'COVER']
    
    @property
    def is_sell_action(self) -> bool:
        """Returns True if this is a sell action (SELL or SHORT)."""
        return self.action in ['SELL', 'SHORT']
    
    @property
    def is_long_side(self) -> bool:
        """Returns True if this is a long-side trade (BUY or SELL)."""
        return self.action in ['BUY', 'SELL']
    
    @property
    def is_short_side(self) -> bool:
        """Returns True if this is a short-side trade (SHORT or COVER)."""
        return self.action in ['SHORT', 'COVER']
    
    def to_order_quantity(self) -> int:
        """
        Convert trade to order quantity with proper sign.
        
        Returns
        -------
        int
            Positive quantity for buy actions, negative for sell actions.
        """
        if self.quantity is None:
            raise ValueError("Cannot convert value-based trade to quantity without price")
        
        if self.is_buy_action:
            return self.quantity
        else:
            return -self.quantity


class TradeList:
    """
    Container for a sequence of trades with utility methods.
    
    Parameters
    ----------
    trades : `list[Trade]`
        List of Trade objects.
    """
    
    def __init__(self, trades: list = None):
        self.trades = trades or []
        self._validate_trades()
    
    def _validate_trades(self):
        """Validate that all trades are properly formed."""
        for i, trade in enumerate(self.trades):
            if not isinstance(trade, Trade):
                raise ValueError(f"Trade at index {i} is not a Trade object")
    
    def add_trade(self, trade: Trade):
        """Add a trade to the list."""
        if not isinstance(trade, Trade):
            raise ValueError("Must provide a Trade object")
        self.trades.append(trade)
    
    def get_trades_for_date(self, date: pd.Timestamp) -> list:
        """
        Get all trades scheduled for a specific date.
        
        Parameters
        ----------
        date : `pd.Timestamp`
            The date to filter trades for.
            
        Returns
        -------
        list[Trade]
            List of trades for the specified date.
        """
        return [trade for trade in self.trades if trade.timestamp.date() == date.date()]
    
    def get_trades_for_asset(self, asset: str) -> list:
        """
        Get all trades for a specific asset.
        
        Parameters
        ----------
        asset : `str`
            The asset symbol to filter for.
            
        Returns
        -------
        list[Trade]
            List of trades for the specified asset.
        """
        return [trade for trade in self.trades if trade.asset == asset]
    
    def get_assets(self) -> set:
        """
        Get all unique assets in the trade list.
        
        Returns
        -------
        set
            Set of unique asset symbols.
        """
        return {trade.asset for trade in self.trades}
    
    def get_date_range(self) -> tuple:
        """
        Get the date range covered by the trades.
        
        Returns
        -------
        tuple[pd.Timestamp, pd.Timestamp]
            Start and end dates of the trade sequence.
        """
        if not self.trades:
            return None, None
        
        timestamps = [trade.timestamp for trade in self.trades]
        return min(timestamps), max(timestamps)
    
    def sort_by_timestamp(self):
        """Sort trades by timestamp in ascending order."""
        self.trades.sort(key=lambda x: x.timestamp)
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert trade list to pandas DataFrame.
        
        Returns
        -------
        pd.DataFrame
            DataFrame representation of the trades.
        """
        if not self.trades:
            return pd.DataFrame()
        
        data = []
        for trade in self.trades:
            data.append({
                'timestamp': trade.timestamp,
                'asset': trade.asset,
                'action': trade.action,
                'quantity': trade.quantity,
                'value': trade.value,
                'price': trade.price,
                'commission': trade.commission,
                'order_id': trade.order_id
            })
        
        return pd.DataFrame(data)
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> 'TradeList':
        """
        Create TradeList from pandas DataFrame.
        
        Parameters
        ----------
        df : `pd.DataFrame`
            DataFrame with trade data. Must have columns: timestamp, asset, action.
            Optional columns: quantity, value, price, commission, order_id.
            
        Returns
        -------
        TradeList
            TradeList object created from the DataFrame.
        """
        required_columns = ['timestamp', 'asset', 'action']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"DataFrame must contain column: {col}")
        
        trades = []
        for _, row in df.iterrows():
            trade = Trade(
                timestamp=pd.to_datetime(row['timestamp']),
                asset=row['asset'],
                action=row['action'],
                quantity=row.get('quantity'),
                value=row.get('value'),
                price=row.get('price'),
                commission=row.get('commission'),
                order_id=row.get('order_id')
            )
            trades.append(trade)
        
        return cls(trades)
    
    @classmethod
    def from_csv(cls, csv_path: str) -> 'TradeList':
        """
        Create TradeList from CSV file.
        
        Parameters
        ----------
        csv_path : `str`
            Path to CSV file containing trade data.
            
        Returns
        -------
        TradeList
            TradeList object created from the CSV file.
        """
        df = pd.read_csv(csv_path)
        return cls.from_dataframe(df)
    
    def __len__(self):
        """Return the number of trades."""
        return len(self.trades)
    
    def __iter__(self):
        """Iterate over trades."""
        return iter(self.trades)
    
    def __getitem__(self, index):
        """Get trade by index."""
        return self.trades[index]
