from typing import Dict
class StaticAllocStrat():
        # A class for managing a static portfolio allocation.
    def __init__(self, allocation: Dict[str, float]): # Constructor method
        # str are the ticker symbols
        # values represent the weights
        if not allocation:
            raise ValueError("dictionary cannot be empty")

        if not isinstance(allocation, dict):
            raise TypeError("allocation must be a dictionary")

        if any(weight <= 0 for weight in allocation.values()):
            raise ValueError("all weights must be greater than zero")

        total_weight = sum(allocation.values())
        if not abs(total_weight - 1.0) < 1e-6:
            raise ValueError("Weights must sum to 1")

        self._allocation = allocation

    def get_tickers(self):
        # returns a list of all tickers
        return list(self._allocation.keys())

    def get_weights(self):
        # returns a list of all weights
        return list(self._allocation.values())

    def get_weight(self, ticker: str):
        # gets the weight of specific ticker
        return self._allocation.get(ticker, None)

    def __getitem__(self, ticker: str):
        # enables dictionary like access to weight
        return self.get_weight(ticker)

    def __iter__(self):
        # allows iteration over tickers
        return iter(self._allocation)

    def __len__(self):
        #returns number of tickers
        return len(self._allocation)

    def __repr__(self):
        # returns a string representation of the object
        return f"StaticAllocStrat({repr(self._allocation)})"
