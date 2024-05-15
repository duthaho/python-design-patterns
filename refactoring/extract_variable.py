class Problem:
    def render_banner(self):
        if (self.platform.upper().index("MAC") > -1 and self.browser.upper().index("IE") > -1 and self.was_initialized() and self.resize > 0):
            # do something
            pass


class Solution:
    def render_banner(self):
        is_mac = self.platform.upper().indexOf("MAC") > -1
        is_ie = self.browser.upper().indexOf("IE") > -1
        was_resized = self.resize > 0

        if is_mac and is_ie and self.was_initialized() and was_resized:
            # do something
            pass
