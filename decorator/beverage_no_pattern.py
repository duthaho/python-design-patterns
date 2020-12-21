class Base:
    COST = 0
    NAME = ''


class Beverage(Base):

    def __init__(self):
        self._condiments = []

    def add_condiment(self, condiment_cls):
        self._condiments.append(condiment_cls)

    def name(self):
        full_name = [self.NAME]
        full_name.extend([condiment.name() for condiment in self._condiments])
        return ', '.join(full_name)

    def cost(self):
        total = self.COST

        for condiment in self._condiments:
            total += condiment.cost()

        return total


class Espresso(Beverage):

    COST = 1.99
    NAME = 'Expresso'


class HouseBlend(Beverage):

    COST = 0.89
    NAME = 'House Blend Coffee'


class Condiment(Base):

    @classmethod
    def name(cls):
        return cls.NAME

    @classmethod
    def cost(cls):
        return cls.COST


class Mocha(Condiment):

    COST = 0.2
    NAME = 'Mocha'


class Whip(Condiment):

    COST = 0.1
    NAME = 'Whip'


if __name__ == "__main__":
    beverage1 = Espresso()
    print(f'{beverage1.name()} ${beverage1.cost()}')

    beverage2 = HouseBlend()
    beverage2.add_condiment(Mocha)
    beverage2.add_condiment(Whip)
    print(f'{beverage2.name()} ${beverage2.cost()}')

    beverage3 = Espresso()
    beverage3.add_condiment(Mocha)
    beverage3.add_condiment(Mocha)
    print(f'{beverage3.name()} ${beverage3.cost()}')
