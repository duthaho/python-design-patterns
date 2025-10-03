from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional


class EventType(Enum):
    PRICE_CHANGE = "price"
    VOLUME_CHANGE = "volume"
    ALL = "all"


class Observer(ABC):
    """Abstract base class for observers with priority support"""

    def __init__(self, priority: int = 999):
        self.priority = priority

    @abstractmethod
    def update(self, subject: "Subject", event_type: EventType) -> None:
        """Called when subject state changes"""
        pass


class Subject(ABC):
    """Abstract base class for subjects (observables)"""

    def __init__(self) -> None:
        self._observers: dict[EventType, list[Observer]] = {
            EventType.PRICE_CHANGE: [],
            EventType.VOLUME_CHANGE: [],
            EventType.ALL: [],
        }

    def attach(
        self, observer: Observer, event_type: EventType = EventType.ALL
    ) -> "Subject":
        """Attach observer to specific event type with priority sorting"""
        if observer not in self._observers[event_type]:
            self._observers[event_type].append(observer)
            # Sort by priority (lower number = higher priority)
            self._observers[event_type].sort(key=lambda obs: obs.priority)
        return self  # Allow chaining

    def detach(
        self, observer: Observer, event_type: EventType = EventType.ALL
    ) -> "Subject":
        """Detach observer from specific event type"""
        if observer in self._observers[event_type]:
            self._observers[event_type].remove(observer)
        return self

    def notify(self, event_type: EventType) -> None:
        """Notify all observers subscribed to event_type or ALL"""
        # Combine specific observers with ALL observers, maintain priority
        observers = self._observers[event_type] + self._observers[EventType.ALL]

        # Remove duplicates while preserving priority order
        seen = set()
        unique_observers = []
        for obs in observers:
            if id(obs) not in seen:
                seen.add(id(obs))
                unique_observers.append(obs)

        # Sort by priority
        unique_observers.sort(key=lambda obs: obs.priority)

        # Notify with error isolation
        for observer in unique_observers:
            try:
                observer.update(self, event_type)
            except Exception as e:
                print(f"❌ Error notifying {observer.__class__.__name__}: {e}")


class StockMarket(Subject):
    """Concrete subject tracking stock market data"""

    def __init__(self, symbol: str = "STOCK") -> None:
        super().__init__()
        self._symbol = symbol
        self._stock_price: float = 0.0
        self._stock_volume: int = 0
        self._timestamp: datetime = datetime.now()

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def stock_price(self) -> float:
        return self._stock_price

    @property
    def stock_volume(self) -> int:
        return self._stock_volume

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def update_stock(self, price: float, volume: int) -> None:
        """Update stock data and notify observers of changes"""
        price_changed = price != self._stock_price
        volume_changed = volume != self._stock_volume

        if not (price_changed or volume_changed):
            return  # No changes, no notifications

        self._stock_price = price
        self._stock_volume = volume
        self._timestamp = datetime.now()

        if price_changed:
            self.notify(EventType.PRICE_CHANGE)
        if volume_changed:
            self.notify(EventType.VOLUME_CHANGE)


class PriceAlertObserver(Observer):
    """Alert on significant price changes (percentage-based)"""

    def __init__(self, threshold_percent: float = 5.0, priority: int = 1) -> None:
        super().__init__(priority)
        self._threshold_percent = threshold_percent
        self._last_price: Optional[float] = None

    def update(self, subject: Subject, event_type: EventType) -> None:
        if isinstance(subject, StockMarket) and event_type == EventType.PRICE_CHANGE:
            current_price = subject.stock_price

            if self._last_price is not None:
                change_percent = abs(
                    (current_price - self._last_price) / self._last_price * 100
                )
                if change_percent > self._threshold_percent:
                    direction = "↑" if current_price > self._last_price else "↓"
                    print(
                        f"🚨 [{subject.symbol}] PriceAlert: {change_percent:.2f}% {direction} "
                        f"(${self._last_price:.2f} → ${current_price:.2f})"
                    )

            self._last_price = current_price


class VolumeAnalyzerObserver(Observer):
    """Analyze and alert on volume thresholds"""

    def __init__(self, min_volume: int, priority: int = 5) -> None:
        super().__init__(priority)
        self._min_volume = min_volume

    def update(self, subject: Subject, event_type: EventType) -> None:
        if isinstance(subject, StockMarket) and event_type == EventType.VOLUME_CHANGE:
            if subject.stock_volume < self._min_volume:
                print(
                    f"📊 [{subject.symbol}] VolumeAnalyzer: Low volume alert! "
                    f"Current: {subject.stock_volume:,} (threshold: {self._min_volume:,})"
                )


class LoggerObserver(Observer):
    """Log all stock market events"""

    def __init__(self, priority: int = 10) -> None:
        super().__init__(priority)

    def update(self, subject: Subject, event_type: EventType) -> None:
        if isinstance(subject, StockMarket):
            timestamp = subject.timestamp.strftime("%H:%M:%S")
            print(
                f"📝 [{subject.symbol}] Logger [{timestamp}] {event_type.value.upper()}: "
                f"Price=${subject.stock_price:.2f}, Volume={subject.stock_volume:,}"
            )


class TradingBotObserver(Observer):
    """High-priority trading bot that reacts to price changes"""

    def __init__(
        self, buy_threshold: float, sell_threshold: float, priority: int = 0
    ) -> None:
        super().__init__(priority)
        self._buy_threshold = buy_threshold
        self._sell_threshold = sell_threshold

    def update(self, subject: Subject, event_type: EventType) -> None:
        if isinstance(subject, StockMarket) and event_type == EventType.PRICE_CHANGE:
            price = subject.stock_price
            if price <= self._buy_threshold:
                print(f"🤖 [{subject.symbol}] TradingBot: BUY signal at ${price:.2f}")
            elif price >= self._sell_threshold:
                print(f"🤖 [{subject.symbol}] TradingBot: SELL signal at ${price:.2f}")


# Demo and Testing
if __name__ == "__main__":
    print("=== Stock Market Observer Pattern Demo ===\n")

    # Create stock market
    market = StockMarket(symbol="AAPL")

    # Create observers with different priorities
    trading_bot = TradingBotObserver(
        buy_threshold=140.0, sell_threshold=160.0, priority=0
    )
    price_alert = PriceAlertObserver(threshold_percent=5.0, priority=1)
    volume_analyzer = VolumeAnalyzerObserver(min_volume=1000, priority=5)
    logger = LoggerObserver(priority=10)

    # Attach observers
    market.attach(trading_bot, EventType.PRICE_CHANGE)
    market.attach(price_alert, EventType.PRICE_CHANGE)
    market.attach(volume_analyzer, EventType.VOLUME_CHANGE)
    market.attach(logger, EventType.ALL)  # Logger gets everything

    print("Initial stock update:")
    market.update_stock(price=150.0, volume=1500)

    print("\n" + "=" * 50)
    print("Price drops (should trigger BUY):")
    market.update_stock(price=135.0, volume=1500)

    print("\n" + "=" * 50)
    print("Volume drops below threshold:")
    market.update_stock(price=135.0, volume=800)

    print("\n" + "=" * 50)
    print("Price spikes (should trigger SELL and alert):")
    market.update_stock(price=165.0, volume=800)

    print("\n" + "=" * 50)
    print("No change (no notifications):")
    market.update_stock(price=165.0, volume=800)

    print("\n=== Demo Complete ===")
