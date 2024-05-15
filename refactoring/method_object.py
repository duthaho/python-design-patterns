class Problem:
    def price(self):
        primary_base_price = 0
        secondary_base_price = 0
        tertiary_basePrice = 0
        # Perform long computation.


class Solution:
    def price(self):
        return PriceCalculator(self).compute()


class PriceCalculator:
    def __init__(self, order):
        self._primaryBasePrice = 0
        self._secondaryBasePrice = 0
        self._tertiaryBasePrice = 0

    def compute(self):
        # Perform long computation.
        pass
