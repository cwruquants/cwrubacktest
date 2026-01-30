import numpy as np


class BacktestDataHandler(object):
    """
    """

    def __init__(
        self,
        universe,
        data_sources=None
    ):
        self.universe = universe
        self.data_sources = data_sources

    def get_asset_latest_bid_price(self, dt, asset_symbol):
        """
        """
        # TODO: Check for asset in Universe
        bid = np.nan
        for ds in self.data_sources:
            try:
                bid = ds.get_bid(dt, asset_symbol)
                if not np.isnan(bid):
                    return bid
            except Exception:
                bid = np.nan
        return bid

    def get_asset_latest_ask_price(self, dt, asset_symbol):
        """
        """
        # TODO: Check for asset in Universe
        ask = np.nan
        for ds in self.data_sources:
            try:
                ask = ds.get_ask(dt, asset_symbol)
                if not np.isnan(ask):
                    return ask
            except Exception:
                ask = np.nan
        return ask

    def get_latest_asset_price(self, dt, asset_symbol):
        """
        Get the latest available price for an asset at the given datetime.
        This is a convenience method that uses the bid price.
        """
        return self.get_asset_latest_bid_price(dt, asset_symbol)

    def get_asset_latest_bid_ask_price(self, dt, asset_symbol):
        """
        """
        # TODO: For the moment this is sufficient for OHLCV
        # data, which only usually provides mid prices
        # This will need to be revisited when handling intraday
        # bid/ask time series.
        # It has been added as an optimisation mechanism for
        # interday backtests.
        bid = self.get_asset_latest_bid_price(dt, asset_symbol)
        return (bid, bid)

    def get_asset_latest_mid_price(self, dt, asset_symbol):
        """
        """
        bid_ask = self.get_asset_latest_bid_ask_price(dt, asset_symbol)
        try:
            mid = (bid_ask[0] + bid_ask[1]) / 2.0
        except Exception:
            # TODO: Log this
            mid = np.nan
        return mid

    def get_assets_historical_range_close_price(
        self, start_dt, end_dt, asset_symbols, adjusted=False
    ):
        """
        """
        prices_df = None
        for ds in self.data_sources:
            try:
                # Check if the data source supports the adjusted parameter
                if hasattr(ds, 'get_assets_historical_closes'):
                    # Get method signature to check if it accepts 'adjusted' parameter
                    import inspect
                    sig = inspect.signature(ds.get_assets_historical_closes)
                    if 'adjusted' in sig.parameters:
                        prices_df = ds.get_assets_historical_closes(
                            start_dt, end_dt, asset_symbols, adjusted=adjusted
                        )
                    else:
                        # Call without adjusted parameter
                        prices_df = ds.get_assets_historical_closes(
                            start_dt, end_dt, asset_symbols
                        )
                    
                    if prices_df is not None:
                        return prices_df
            except Exception:
                raise
        return prices_df