from abc import abstractmethod, ABC
from typing import Type


class BaseButton(ABC):
    @abstractmethod
    def render(self):
        pass


class WinButton(BaseButton):
    def render(self):
        print("Render window button")


class IosButton(BaseButton):
    def render(self):
        print("Render iOS button")


class BaseCheckbox(ABC):
    @abstractmethod
    def render(self):
        pass


class WinCheckbox(BaseCheckbox):
    def render(self):
        print("Render window checkbox")


class IosCheckbox(BaseCheckbox):
    def render(self):
        print("Render iOS checkbox")


class GuiFactory(ABC):
    @classmethod
    @abstractmethod
    def create_button(cls) -> BaseButton:
        pass

    @classmethod
    @abstractmethod
    def create_checkbox(cls) -> BaseCheckbox:
        pass


class WindowFactory(GuiFactory):
    @classmethod
    def create_button(cls) -> BaseButton:
        return WinButton()

    @classmethod
    def create_checkbox(cls) -> BaseCheckbox:
        return WinCheckbox()


class IosFactory(GuiFactory):
    @classmethod
    def create_button(cls) -> BaseButton:
        return IosButton()

    @classmethod
    def create_checkbox(cls) -> BaseCheckbox:
        return IosCheckbox()


class Application:
    def __init__(self):
        self.factory = self.get_factory()
        self.button = self.factory.create_button()
        self.checkbox = self.factory.create_checkbox()

    def get_factory(self) -> Type[GuiFactory]:
        config = self.get_config()
        if config.get("OS") == "Windows":
            return WindowFactory
        return IosFactory

    def get_config(self) -> dict:  # noqa
        return {}

    def render(self):
        self.button.render()
        self.checkbox.render()


if __name__ == "__main__":
    app = Application()
    app.render()
