"""
Intent:
Define a one-to-many dependency between objects so that when one object changes state, all its
dependents are notified and updated automatically.

Problem:
Imagine you’re developing a news application that allows users to subscribe to different news categories
(such as sports, technology, and politics). When a new article is published in a category, all users
subscribed to that category should be notified of the new article. Implementing this functionality can
be complex, especially if you want to maintain the integrity of the notification system without tightly
coupling the news publisher and subscribers.

Solution:
The Observer pattern suggests creating a subject (the news publisher) that maintains a list of observers
(the subscribers) and provides methods to attach, detach, and notify observers. When the subject's
state changes (e.g., a new article is published), it notifies all registered observers by calling their
update methods. This allows for a loose coupling between the subject and its observers, as the subject
does not need to know the details of the observers.

When to use:
- When you need to implement a notification system where multiple objects need to be informed of
    changes in another object.
- When you want to maintain a loose coupling between the subject and its observers, allowing for
    flexibility and scalability.
- When you want to implement a publish-subscribe mechanism where observers can dynamically
    subscribe or unsubscribe from notifications.
- When you want to ensure that all observers are updated automatically when the subject's state
    changes.
- When you want to avoid tight coupling between the subject and its observers, allowing for easier
    maintenance and modification of the code.

How to implement:
1. Identify the subject (the object whose state changes) and the observers (the objects that need to
    be notified of changes).
2. Create an interface or abstract class for the observer that defines the update method, which will
    be called when the subject's state changes.
3. Create a concrete implementation of the subject that maintains a list of observers and provides
    methods to attach, detach, and notify observers.
4. In the subject's state-changing methods, call the notify method to inform all registered observers
    of the change.
5. Create concrete implementations of the observer that implement the update method to handle
    notifications from the subject.

Pros and Cons:
+ Provides a way to maintain a loose coupling between the subject and its observers, allowing for
    flexibility and scalability.
+ Simplifies the implementation of notification systems in applications.
+ Allows for dynamic subscription and unsubscription of observers, making it easy to manage
    notifications.
- Can introduce additional complexity by adding more classes (subject and observers).
- May lead to performance issues if there are many observers and frequent state changes in the subject.
- Can make the code harder to understand if not implemented carefully, especially if there are
    many observers with complex update logic.
- May require careful management of observer lifetimes to avoid memory leaks or excessive memory usage.
- Can lead to a proliferation of observer objects if many different types of observers are needed.
- May not be suitable for all types of applications, especially those with simple notification needs.
- Can lead to unexpected behavior if observers modify the subject's state during notification,
    potentially causing infinite loops or inconsistent states.

Real-world use cases:
- In user interface frameworks, the Observer pattern is often used to implement event handling
    systems, where UI components (observers) need to be notified of user actions (subject).
- In social media applications, the Observer pattern can be used to implement follower systems,
    where users (observers) are notified of updates from the accounts they follow (subject).
- In stock market applications, the Observer pattern can be used to notify investors (observers)
    of changes in stock prices (subject).
- In messaging applications, the Observer pattern can be used to implement chat systems, where
    users (observers) are notified of new messages in chat rooms (subject).
- In real-time data monitoring systems, the Observer pattern can be used to notify monitoring
    dashboards (observers) of changes in data sources (subject).
"""

# Link: https://refactoring.guru/design-patterns/observer


from abc import ABC, abstractmethod


class Subject(ABC):
    @abstractmethod
    def attach(self, observer: "Observer") -> None:
        pass

    @abstractmethod
    def detach(self, observer: "Observer") -> None:
        pass

    @abstractmethod
    def notify(self) -> None:
        pass


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        pass


class NewsPublisher(Subject):
    def __init__(self) -> None:
        self._observers: set[Observer] = set()
        self._latest_news: str = ""

    def attach(self, observer: Observer) -> None:
        self._observers.add(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.discard(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)

    def publish_news(self, news: str) -> None:
        self._latest_news = news
        self.notify()

    @property
    def latest_news(self) -> str:
        return self._latest_news


class NewsSubscriber(Observer):
    def __init__(self, name: str) -> None:
        self._name = name

    def update(self, subject: Subject) -> None:
        if isinstance(subject, NewsPublisher):
            print(f"{self._name} received news update: {subject.latest_news}")


if __name__ == "__main__":
    publisher = NewsPublisher()

    subscriber1 = NewsSubscriber("Alice")
    subscriber2 = NewsSubscriber("Bob")

    publisher.attach(subscriber1)
    publisher.attach(subscriber2)

    publisher.publish_news("Breaking News: Observer Pattern Implemented!")

    publisher.detach(subscriber1)

    publisher.publish_news("Update: Observer Pattern Example Completed!")
