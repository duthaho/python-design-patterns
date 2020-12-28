from abc import ABC, abstractmethod


class Factory:
    TYPE = {}

    @classmethod
    def create(cls, type):
        return cls.TYPE.get(type)


class PizzaType:
    CHEESE = 1
    PEPPERON = 2
    CLAM = 3
    VEGGIE = 4


class BasePizza(ABC):
    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    def bake(self):
        pass

    @abstractmethod
    def cut(self):
        pass

    @abstractmethod
    def box(self):
        pass


class CheesePizza(BasePizza):
    def prepare(self):
        print(f'{self.__class__.__name__}.prepare')

    def bake(self):
        print(f'{self.__class__.__name__}.bake')

    def cut(self):
        print(f'{self.__class__.__name__}.cut')

    def box(self):
        print(f'{self.__class__.__name__}.box')


class PepperonPizza(BasePizza):
    def prepare(self):
        print(f'{self.__class__.__name__}.prepare')

    def bake(self):
        print(f'{self.__class__.__name__}.bake')

    def cut(self):
        print(f'{self.__class__.__name__}.cut')

    def box(self):
        print(f'{self.__class__.__name__}.box')


class ClamPizza(BasePizza):
    def prepare(self):
        print(f'{self.__class__.__name__}.prepare')

    def bake(self):
        print(f'{self.__class__.__name__}.bake')

    def cut(self):
        print(f'{self.__class__.__name__}.cut')

    def box(self):
        print(f'{self.__class__.__name__}.box')


class VeggiePizza(BasePizza):
    def prepare(self):
        print(f'{self.__class__.__name__}.prepare')

    def bake(self):
        print(f'{self.__class__.__name__}.bake')

    def cut(self):
        print(f'{self.__class__.__name__}.cut')

    def box(self):
        print(f'{self.__class__.__name__}.box')


class PizzaFactory(Factory):
    TYPE = {
        PizzaType.CHEESE: CheesePizza,
        PizzaType.PEPPERON: PepperonPizza,
        PizzaType.CLAM: ClamPizza,
        PizzaType.VEGGIE: VeggiePizza,
    }


class BaseStore(ABC):
    def __init__(self, factory_cls=None):
        self._factory_cls = factory_cls or self.default_factory()

    def default_factory(self):
        pass

    @property
    def factory(self):
        return self._factory_cls

    @factory.setter
    def factory(self, factory_cls):
        self._factory_cls = factory_cls

    def create(self, type):
        if self._factory_cls:
            product_cls = self._factory_cls.create(type)
            return product_cls() if product_cls else None

    def order(self, type):
        pass


class PizzaStore(BaseStore):
    def order(self, type):
        pizza = self.create(type)
        if pizza:
            pizza.prepare()
            pizza.bake()
            pizza.cut()
            pizza.box()
        return pizza


if __name__ == "__main__":
    pizza_store = PizzaStore(PizzaFactory)

    pizza1 = pizza_store.order(PizzaType.VEGGIE)
    pizza2 = pizza_store.order(PizzaType.CHEESE)
