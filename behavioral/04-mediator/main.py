"""
Intent:
Mediator is a behavioral design pattern that defines an object (the mediator) that encapsulates how
a set of objects interact. This pattern promotes loose coupling by preventing objects from
referring to each other explicitly, allowing their interaction to be varied independently.

Problem:
In a complex system, objects often need to communicate with each other. If each object directly
references and interacts with other objects, it can lead to a tangled web of dependencies. This
makes the system hard to maintain, understand, and extend. The Mediator pattern addresses this
issue by introducing a mediator object that handles the communication between different objects,
thus reducing the dependencies between them.

Solution:
The Mediator pattern suggests creating a mediator object that acts as an intermediary between
the various objects in the system. Instead of objects communicating directly with each other,
they communicate through the mediator. The mediator is responsible for coordinating the interactions
between the objects, ensuring that they remain decoupled. This allows for easier maintenance and
extension of the system, as changes to one object do not directly affect others.

When to Use:
- When you have a complex system with many interacting objects that need to communicate with
    each other.
- When you want to reduce the dependencies between objects and promote loose coupling.
- When you want to centralize the communication logic in a single place (the mediator) rather
    than spreading it across multiple objects.
- When you want to make it easier to maintain and extend the system by isolating changes to
    individual objects.
- When you want to implement complex interaction logic that involves multiple objects.
- When you want to improve the readability and understandability of the system by reducing
    direct interactions between objects.
- When you want to facilitate communication between objects that may not be aware of each
    other.
- When you want to implement a publish-subscribe mechanism where objects can subscribe to
    events and be notified by the mediator.

How to Implement:
1. Define a mediator interface that declares methods for communication between objects.
2. Create concrete mediator classes that implement the mediator interface. Each mediator
    should maintain references to the objects it coordinates and implement the communication logic.
3. Define a colleague interface that declares methods for communication with the mediator.
4. Create concrete colleague classes that implement the colleague interface. Each colleague
    should maintain a reference to the mediator and use it to communicate with other colleagues.
5. In the client code, create instances of the concrete mediator and colleague classes. Set
    up the relationships between the mediator and colleagues.
6. Use the mediator to facilitate communication between colleagues, ensuring that they do not
    interact directly with each other.
7. Optionally, implement additional features in the mediator, such as logging or validation,
    to enhance the communication process.
8. Consider implementing different types of mediators for various communication strategies
    (e.g., event-based, command-based).
9. Ensure that the mediator can handle changes to the colleagues, such as adding or removing
    colleagues dynamically.

Pros and Cons:
+ Promotes loose coupling between objects by reducing direct dependencies.
+ Centralizes communication logic in a single place (the mediator).
+ Makes it easier to maintain and extend the system by isolating changes to individual objects.
+ Improves readability and understandability of the system by reducing direct interactions
    between objects.
+ Facilitates communication between objects that may not be aware of each other.
- May introduce a single point of failure if the mediator becomes too complex or is not well-designed.
- Can lead to performance overhead due to the additional layer of abstraction.
- May require careful design to ensure that the mediator and colleague interfaces are compatible.
- Can lead to issues if the mediator becomes a "god object" that knows too much about the
    colleagues and their interactions.
- May require additional effort to implement and maintain the mediator and colleague classes.
- Can lead to challenges in debugging and tracing interactions, as the communication is
    centralized in the mediator rather than being distributed among the objects.
- May not be suitable for simple systems where direct communication between objects is sufficient.
- Can lead to increased complexity if the mediator has to handle a large number of colleagues
    and interactions.
- May require additional testing to ensure that the mediator correctly handles all interactions
    between colleagues.
- Can lead to challenges in scaling the system if the mediator becomes a bottleneck for
    communication.

Real-world use cases:
- Implementing chat applications where a central server (mediator) manages communication
    between multiple clients (colleagues).
- Implementing air traffic control systems where a central controller (mediator) coordinates
    communication between multiple aircraft (colleagues).
- Implementing GUI frameworks where a central event dispatcher (mediator) manages events
    between various UI components (colleagues).
- Implementing workflow management systems where a central coordinator (mediator) manages
    tasks between different services or components (colleagues).
- Implementing multiplayer online games where a central game server (mediator) manages
    interactions between multiple players (colleagues).
- Implementing IoT systems where a central hub (mediator) manages communication between
    various devices (colleagues).
- Implementing customer support systems where a central ticketing system (mediator) manages
    communication between support agents and customers (colleagues).
- Implementing event-driven architectures where a central event bus (mediator) manages
    communication between various services (colleagues).
- Implementing microservices architectures where an API gateway (mediator) manages communication
    between different microservices (colleagues).
- Implementing real-time collaboration tools where a central server (mediator) manages
    communication between multiple users (colleagues).
"""

# Link: https://refactoring.guru/design-patterns/mediator


from abc import ABC, abstractmethod


class Mediator(ABC):
    @abstractmethod
    def notify(self, sender: str, event: str, payload: dict | None = None) -> None: ...


class Colleague(ABC):
    def __init__(self, mediator: Mediator) -> None:
        self.mediator = mediator


class SignupButton(Colleague):
    def __init__(self, mediator: Mediator) -> None:
        super().__init__(mediator)
        self.enabled = False

    def enable(self) -> None:
        self.enabled = True
        print("[Button] Enabled")

    def disable(self) -> None:
        self.enabled = False
        print("[Button] Disabled")


class UsernameField(Colleague):
    def set_value(self, value: str) -> None:
        print(f"[UsernameField] Changed: {value}")
        self.mediator.notify(
            sender="username", event="changed", payload={"value": value}
        )

    def show_error(self, message: str) -> None:
        print(f"[UsernameField] Error: {message}")


class PasswordField(Colleague):
    def set_value(self, value: str) -> None:
        print(f"[PasswordField] Changed")
        self.mediator.notify(
            sender="password", event="changed", payload={"value": value}
        )

    def show_error(self, message: str) -> None:
        print(f"[PasswordField] Error: {message}")


class FormMediator(Mediator):
    def __init__(self) -> None:
        self.username: str = ""
        self.password: str = ""
        self.existing = {"duong", "admin", "user"}
        # will be set after creation
        self.username_field: UsernameField | None = None
        self.password_field: PasswordField | None = None
        self.button: SignupButton | None = None

    def register(
        self,
        username_field: UsernameField,
        password_field: PasswordField,
        button: SignupButton,
    ) -> None:
        self.username_field = username_field
        self.password_field = password_field
        self.button = button

    def notify(self, sender: str, event: str, payload: dict | None = None) -> None:
        if sender == "username" and event == "changed":
            self.username = payload["value"]
            if self.username in self.existing:
                self.username_field.show_error("Username already exists")
            else:
                print("[UsernameField] Username is available")
        elif sender == "password" and event == "changed":
            self.password = payload["value"]
            if len(self.password) < 8:
                self.password_field.show_error("Password too short")
            elif not any(char.isdigit() for char in self.password):
                self.password_field.show_error("Password must contain a number")
            elif not any(char.isupper() for char in self.password):
                self.password_field.show_error(
                    "Password must contain an uppercase letter"
                )
            elif not any(char in "!@#$%^&*()-_+=" for char in self.password):
                self.password_field.show_error(
                    "Password must contain a special character"
                )
            else:
                print("[PasswordField] Password is strong")
        # Enable button if both username and password are valid
        if (
            self.username
            and self.username not in self.existing
            and self.password
            and len(self.password) >= 8
            and any(char.isdigit() for char in self.password)
            and any(char.isupper() for char in self.password)
            and any(char in "!@#$%^&*()-_+=" for char in self.password)
        ):
            self.button.enable()
        else:
            self.button.disable()


def main():
    mediator = FormMediator()
    username = UsernameField(mediator)
    password = PasswordField(mediator)
    button = SignupButton(mediator)
    mediator.register(username, password, button)

    username.set_value("duong")  # existing -> error, button disabled
    password.set_value("Weak1")  # too short -> error, button disabled
    username.set_value("new_user")  # ok
    password.set_value("Strong!Pass123")  # ok -> button enabled


if __name__ == "__main__":
    main()
