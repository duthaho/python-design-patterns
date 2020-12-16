from abc import ABC, abstractmethod

from base import Observer, Subject


class WeatherData(Subject):

    def __init__(self):
        super().__init__()
        self._temperature = 0
        self._humidity = 0
        self._pressure = 0

    def state(self):
        return dict(
            temperature=self._temperature,
            humidity=self._humidity,
            pressure=self._pressure,
        )

    def measurement_changed(self):
        self._changed = True
        self.notify()

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, val):
        self._temperature = val

    @property
    def humidity(self):
        return self._humidity

    @humidity.setter
    def humidity(self, val):
        self._humidity = val

    @property
    def pressure(self):
        return self._pressure

    @pressure.setter
    def pressure(self, val):
        self._pressure = val


class BaseDisplay(ABC):

    @abstractmethod
    def display(self):
        pass


class CurrentConditions(Observer, BaseDisplay):

    def __init__(self):
        self._temperature = 0
        self._humidity = 0

    def update(self, subject, **kwargs):
        if isinstance(subject, WeatherData):
            self._temperature = kwargs.get('temperature')
            self._humidity = kwargs.get('humidity')
        self.display()

    def display(self):
        print(f'Current coditions: {self._temperature}F degrees and {self._humidity}% humidity')


class StatisticsDisplay(Observer, BaseDisplay):

    def update(self, subject, **kwargs):
        self.display()

    def display(self):
        print('Statistics')


class ForecastDisplay(Observer, BaseDisplay):

    def update(self, subject, **kwargs):
        self.display()

    def display(self):
        print('Forecast')


if __name__ == "__main__":
    data = WeatherData()

    display_1 = CurrentConditions()
    display_2 = StatisticsDisplay()
    display_3 = ForecastDisplay()

    data.register(display_1)
    data.register(display_2)
    data.register(display_3)

    data.temperature = 20
    data.humidity = 90
    data.measurement_changed()

    data.remove(display_1)
    data.temperature = 30
    data.measurement_changed()
