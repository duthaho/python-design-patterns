from abc import abstractmethod, ABC
from typing import Optional


class Car:
    def __init__(self):
        self.seat = 0
        self.engine = ""
        self.trip_computer = False
        self.gps = False

    def info(self):
        print(f"Car: {self.seat} - {self.engine} - {self.trip_computer} - {self.gps}")


class Builder(ABC):
    def __init__(self):
        self._car = None
        self.reset()

    @abstractmethod
    def reset(self) -> "Builder":
        pass

    @abstractmethod
    def set_seat(self, seat: int) -> "Builder":
        pass

    @abstractmethod
    def set_engine(self, engine: str) -> "Builder":
        pass

    @abstractmethod
    def set_trip_computer(self) -> "Builder":
        pass

    @abstractmethod
    def set_gps(self) -> "Builder":
        pass

    @abstractmethod
    def get(self) -> Car:
        pass


class CarBuilder(Builder):
    def reset(self) -> "Builder":
        self._car = Car()
        return self

    def set_seat(self, seat: int) -> "Builder":
        self._car.seat = seat
        return self

    def set_engine(self, engine: str) -> "Builder":
        self._car.engine = engine
        return self

    def set_trip_computer(self) -> "Builder":
        self._car.trip_computer = True
        return self

    def set_gps(self) -> "Builder":
        self._car.gps = True
        return self

    def get(self) -> Car:
        return self._car


class Director:
    def __init__(self):
        self._builder: Optional[Builder] = None

    @property
    def builder(self) -> Builder:
        return self._builder

    @builder.setter
    def builder(self, builder: Builder):
        self._builder = builder

    def build_sport_car(self) -> Car:
        self._builder.reset().set_seat(2).set_engine("sport").set_trip_computer().set_gps()
        return self._builder.get()

    def build_suv(self) -> Car:
        self._builder.reset().set_seat(4).set_gps()
        return self._builder.get()


class Application:
    def make_car(self):
        director = Director()

        car_builder = CarBuilder()
        director.builder = car_builder
        car = director.build_suv()
        car.info()

        car = director.build_sport_car()
        car.info()


if __name__ == "__main__":
    app = Application()
    app.make_car()
