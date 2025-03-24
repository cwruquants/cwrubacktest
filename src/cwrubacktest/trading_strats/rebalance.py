import pandas as pd
from pandas.tseries.offsets import BusinessDay
import pytz
from enum import Enum

class RebalancePeriod(Enum):
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
    NEVER = 4

class RebalanceGenerator():
    """
    Generates a list of rebalance timestamps for pre- or post-market,
    for the final calendar day of the month between the starting and
    ending dates provided.

    All timestamps produced are set to UTC.

    Parameters
    ----------
    start_dt : `pd.Timestamp`
        The starting datetime of the rebalance range.
    end_dt : `pd.Timestamp`
        The ending datetime of the rebalance range.
    pre_market : `Boolean`, optional
        Whether to carry out the rebalance at market open/close on
        the final day of the month. Defaults to False, i.e at
        market close.
    """

    def __init__(
        self,
        start_dt,
        end_dt,
        rebal_pd: RebalancePeriod,
        pre_market=False
    ):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.rebal_pd = rebal_pd
        self.market_time = self._set_market_time(pre_market)
        self.rebalances = self._generate_rebalances()

    def _is_business_day(self):
        """
        Checks if the start_dt is a business day.
        
        Returns
        -------
        `boolean`
        """
        return bool(len(pd.bdate_range(self.start_dt, self.start_dt)))

    def _set_market_time(self, pre_market):
        """
        Determines whether to use market open or market close
        as the rebalance time.

        Parameters
        ----------
        pre_market : `Boolean`
            Whether the rebalance is carried out at market open/close.

        Returns
        -------
        `str`
            The time string used for Pandas timestamp construction.
        """
        return "14:30:00" if pre_market else "21:00:00"

    def _generate_rebalances(self):
        """
        Utilise the Pandas date_range method to create the appropriate
        list of rebalance timestamps.

        Returns
        -------
        `List[pd.Timestamp]`
            The list of rebalance timestamps.
        """

        match self.rebal_pd:
            case RebalancePeriod.DAILY:
                rebalance_dates = pd.bdate_range(
                    start=self.start_dt, end=self.end_dt,
                )

                rebalance_times = [
                    pd.Timestamp(
                        "%s %s" % (date, self.market_time), tz=pytz.utc
                    )
                    for date in rebalance_dates
                ]

                return rebalance_times

            case RebalancePeriod.WEEKLY:
                rebalance_dates = pd.date_range(
                    start=self.start_dt,
                    end=self.end_dt,
                    freq='W-%s' % self.weekday
                )

                rebalance_times = [
                    pd.Timestamp(
                        "%s %s" % (date, self.pre_market_time), tz=pytz.utc
                    )
                    for date in rebalance_dates
                ]

                return rebalance_times

            case RebalancePeriod.MONTHLY:
                rebalance_dates = pd.date_range(
                    start=self.start_dt,
                    end=self.end_dt,
                    freq='BME'
                )

                rebalance_times = [
                    pd.Timestamp(
                        "%s %s" % (date, self.market_time), tz=pytz.utc
                    )
                    for date in rebalance_dates
                ]
                return rebalance_times
            
            case RebalancePeriod.NEVER:
                if not self._is_business_day():
                    rebalance_date = self.start_dt + BusinessDay()
                else:
                    rebalance_date = self.start_dt
                return [rebalance_date]