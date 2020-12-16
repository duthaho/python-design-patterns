from abc import ABC, abstractmethod


class Observer(ABC):

    @abstractmethod
    def update(self, subject, **kwargs):
        pass


class Subject(ABC):

    def __init__(self):
        self._changed = False
        self._observers = []

    @property
    def changed(self):
        return self._changed

    @changed.setter
    def changed(self, val):
        self._changed = val

    @abstractmethod
    def state(self):
        pass

    def register(self, observer: Observer):
        self._observers.append(observer)

    def remove(self, observer: Observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self):
        if not self._changed:
            return

        for observer in self._observers:
            observer.update(self, **self.state())

        self._changed = False
