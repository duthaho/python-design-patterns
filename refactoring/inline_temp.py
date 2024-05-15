class Problem:
    def has_discount(self):
        base_price = self.base_price()
        return base_price > 1000


class Solution:
    def has_discount(self):
        return self.base_price() > 1000
