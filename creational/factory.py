from abc import abstractmethod, ABC


class BaseButton(ABC):
    @abstractmethod
    def render(self):
        pass

    @abstractmethod
    def on_click(self):
        pass


class WindowsButton(BaseButton):
    def render(self):
        print("Render window button")

    def on_click(self):
        print("On click")


class HtmlButton(BaseButton):
    def render(self):
        print("Render html button")

    def on_click(self):
        print("On click")


class BaseDialog(ABC):
    @abstractmethod
    def create_button(self) -> BaseButton:
        pass

    def render(self):
        ok_btn = self.create_button()
        ok_btn.render()


class WindowsDialog(BaseDialog):
    def create_button(self) -> BaseButton:
        return WindowsButton()


class WebDialog(BaseDialog):
    def create_button(self) -> BaseButton:
        return HtmlButton()


class Application:
    def __init__(self):
        self.dialog = self.get_dialog()

    def read_config(self) -> dict:  # noqa
        return {}

    def get_dialog(self) -> BaseDialog:
        config: dict = self.read_config()
        if config.get("OS") == "Windows":
            return WindowsDialog()
        return WebDialog()

    def render(self):
        self.dialog.render()


if __name__ == "__main__":
    app = Application()
    app.render()
