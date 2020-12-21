from abc import ABC


class Beverage(ABC):

    COST = 0
    NAME = ''

    def name(self):
        return self.NAME

    def cost(self):
        return self.COST


class Decorator(Beverage):

    def __init__(self, beverage: Beverage):
        self._beverage = beverage

    def name(self):
        return f'{self._beverage.name()}, {self.NAME}'

    def cost(self):
        return self._beverage.cost() + self.COST


class Espresso(Beverage):

    COST = 1.99
    NAME = 'Expresso'


class HouseBlend(Beverage):

    COST = 0.89
    NAME = 'House Blend Coffee'


class Mocha(Decorator):

    COST = 0.2
    NAME = 'Mocha'


class Whip(Decorator):

    COST = 0.1
    NAME = 'Whip'


if __name__ == "__main__":
    beverage1 = Espresso()
    print(f'{beverage1.name()} ${beverage1.cost()}')

    beverage2 = HouseBlend()
    beverage2 = Mocha(beverage2)
    beverage2 = Whip(beverage2)
    print(f'{beverage2.name()} ${beverage2.cost()}')

    beverage3 = Espresso()
    beverage3 = Mocha(beverage3)
    beverage3 = Mocha(beverage3)
    print(f'{beverage3.name()} ${beverage3.cost()}')
