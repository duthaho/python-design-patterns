class Problem:
    def print_owing(self):
        self.print_banner()

        # print details
        print("name:", self.name)
        print("amount:", self.get_outstanding())


class Solution:
    def print_owing(self):
        self.print_banner()
        self.print_details(self.get_outstanding())

    def print_details(self, outstanding):
        print("name:", self.name)
        print("amount:", outstanding)
