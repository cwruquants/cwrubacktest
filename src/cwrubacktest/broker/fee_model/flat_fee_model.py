from cwrubacktest.broker.fee_model.abs_fee_model import FeeModel

class flat_fee_model(FeeModel):
    '''
    Done by Monish Sinha
    A FeeModel subclass that produces a flat rate cost per share

    Parameters
    ----------
    fee_per_share : `float`, optional
        The flat fee charged per share traded.
        Defaults to 0.0 if not specified.
    tax_per_share : `float`, optional
        The flat tax charged per share traded.
        Defaults to 0.0 if not specified.
    '''

    def __init__(self, fee_per_share=0.0, tax_per_share=0.0):
        super().__init__()
        self.fee_per_share = fee_per_share
        self.tax_per_share = tax_per_share

    def _calc_commission(self, asset, quantity, consideration, broker=None):
        """
        Calculate the commission based on a flat rate per share.

        Parameters
        ----------
        asset : `str`
            The asset symbol string.
        quantity : `int`
            The quantity of assets traded.
        consideration : `float`
            Price times quantity of the order.
        broker : `Broker`, optional
            An optional Broker reference.

        Returns
        -------
        `float`
            The total commission calculated as fee per share times quantity.
        """
        return abs(quantity) * self.fee_per_share

    def _calc_tax(self, asset, quantity, consideration, broker=None):
        """
                Calculate the tax based on a flat rate per share.

                Parameters
                ----------
                asset : `str`
                    The asset symbol string.
                quantity : `int`
                    The quantity of assets traded.
                consideration : `float`
                    Price times quantity of the order.
                broker : `Broker`, optional
                    An optional Broker reference.

                Returns
                -------
                `float`
                    The total tax calculated as tax per share times quantity.
                """
        return abs(quantity) * self.tax_per_share

    def calc_total_cost(self, asset, quantity, consideration, broker=None):
        """
        Calculate the total commission and tax for the trade.

        Parameters
        ----------
        asset : `str`
            The asset symbol string.
        quantity : `int`
            The quantity of assets traded.
        consideration : `float`
            Price times quantity of the order.
        broker : `Broker`, optional
            An optional Broker reference.

        Returns
        -------
        `float`
            The total commission and tax.
        """
        commission = self._calc_commission(asset, quantity, consideration, broker)
        tax = self._calc_tax(asset, quantity, consideration, broker)
        return commission + tax
