from typing import Dict
class StaticAllocStrat():
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
        return list(self._allocation.keys())

    def get_weights(self):
        return list(self._allocation.values())

    def get_weight(self, ticker: str):
        return self._allocation.get(ticker, None)

    def __getitem__(self, ticker: str):
        return self.get_weight(ticker)

    def __iter__(self):
        return iter(self._allocation)

    def __len__(self):
        return len(self._allocation)

    def __repr__(self):
        return f"StaticAllocStrat({repr(self._allocation)})"
