class Problem:
    def get_rating(self):
        return 2 if self.more_than_5_late_deliveries() else 1

    def more_than_5_late_deliveries(self):
        return self.number_of_late_deliveries > 5


class Solution:
    def get_rating(self):
        return 2 if self.number_of_late_deliveries > 5 else 1
