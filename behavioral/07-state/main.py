"""
Intent:
Allow an object to alter its behavior when its internal state changes. The object will appear to change
its class.

Problem:
Imagine you are developing a text editor application that supports multiple modes of operation, such as
insert mode, command mode, and visual mode. Each mode has its own set of behaviors and commands. For
example, in insert mode, typing characters adds them to the document, while in command mode, typing
certain keys executes commands like saving or quitting the document. Implementing this functionality
can lead to complex conditional statements scattered throughout the code, making it difficult to
maintain and extend.

Solution:
The State pattern suggests creating separate state classes for each mode of operation, encapsulating
the behaviors associated with that mode. The main text editor class maintains a reference to the current
state and delegates behavior to the current state object. When the mode changes, the text editor
simply switches its current state to the appropriate state object. This approach eliminates the need
for complex conditional statements and makes it easier to add new modes in the future.

When to use:
- When an object's behavior depends on its state, and it must change its behavior at runtime based
    on that state.
- When you want to avoid large conditional statements that check the object's state and execute
    different behaviors based on that state.
- When you want to encapsulate state-specific behavior in separate classes, making it easier to
    maintain and extend the code.
- When you want to allow an object to change its behavior dynamically at runtime without changing
    its class.
- When you want to improve code readability and maintainability by separating state-specific
    behavior into distinct classes.
- When you want to implement a finite state machine where an object can transition between different
    states based on events or conditions.
- When you want to avoid tight coupling between the context (the main object) and its states,
    allowing for greater flexibility and scalability.
- When you want to adhere to the Open/Closed Principle, allowing new states to be added without
    modifying existing code.

How to implement:
1. Identify the different states that the object can be in and the behaviors associated with each
    state.
2. Create an interface or abstract class for the state that defines the methods for the behaviors
    associated with that state.
3. Create concrete state classes that implement the state interface and provide the specific
    implementations for the behaviors associated with that state.
4. Create a context class (the main object) that maintains a reference to the current state
    and delegates behavior to the current state object.
5. Implement methods in the context class to change the current state, allowing the object to
    transition between different states.
6. In the context class, ensure that all behavior methods delegate to the current state object,
    allowing the behavior to change dynamically based on the current state.

Pros and Cons:
+ Encapsulates state-specific behavior in separate classes, improving code organization and
    maintainability.
+ Eliminates the need for complex conditional statements, making the code easier to read and
    understand.
+ Allows for dynamic behavior changes at runtime without changing the object's class.
+ Adheres to the Open/Closed Principle, allowing new states to be added without modifying existing
    code.
- Can introduce additional complexity by adding more classes (state classes).
- May lead to performance overhead due to the increased number of objects and method calls.
- Can make the code harder to understand if not implemented carefully, especially if there are
    many states with complex behaviors.
- May require careful management of state transitions to avoid invalid states or inconsistent
    behavior.
- Can lead to a proliferation of state classes if many different states are needed.
- May not be suitable for all types of applications, especially those with simple state management
    needs.
- Can lead to unexpected behavior if state transitions are not handled properly, potentially causing
    infinite loops or inconsistent states.

Real-world use cases:
- Text editors with multiple modes of operation (insert, command, visual).
- Vending machines that change behavior based on the current state (waiting for selection,
    dispensing item, out of stock).
- Traffic light systems that change behavior based on the current state (red, yellow, green).
- Media players that change behavior based on the current state (playing, paused, stopped).
- Game characters that change behavior based on the current state (idle, walking, running,
    attacking).
- Network connections that change behavior based on the current state (connected, disconnected,
    reconnecting).
- Document editors that change behavior based on the current state (editing, reviewing, commenting).
- Workflow systems that change behavior based on the current state (draft, submitted, approved,
    rejected).
- User authentication systems that change behavior based on the current state (logged out,
    logged in, locked).
- Order processing systems that change behavior based on the current state (pending, processed,
    shipped, delivered).
- State machines in various applications, such as parsers, protocol handlers, and game AI.
- UI components that change behavior based on the current state (enabled, disabled, focused,
    hovered).
"""

# Link: https://refactoring.guru/design-patterns/state


from abc import ABC, abstractmethod


class Document:
    def __init__(self) -> None:
        self.content = ""
        self.state: "State" = DraftState()

    def render(self) -> str:
        return self.state.render(self)

    def write(self, text: str) -> None:
        if self.state.writeable():
            self.content += text
        else:
            print("Document is not writeable in the current state.")

    def edit(self, new_content: str) -> None:
        if self.state.editable():
            self.content = new_content
        else:
            print("Document is not editable in the current state.")

    def publish(self) -> None:
        if self.state.publishable():
            self.state = self.state.publish(self)
        else:
            print("Document cannot be published in the current state.")

    def approve(self) -> None:
        self.state = self.state.approve(self)

    def reject(self) -> None:
        self.state = self.state.reject(self)

    def save(self) -> dict:
        return {"content": self.content, "state": self.state.NAME}
    
    @classmethod
    def load(cls, data: dict) -> "Document":
        new_doc = cls()
        new_doc.content = data["content"]
        state_name = data["state"]
        states = {
            DraftState.NAME: DraftState(),
            ModerationState.NAME: ModerationState(),
            PublishedState.NAME: PublishedState(),
        }
        new_doc.state = states.get(state_name, DraftState())
        return new_doc



class State(ABC):
    NAME: str

    @abstractmethod
    def render(self, document: Document) -> str:
        pass

    @abstractmethod
    def publish(self, document: Document) -> "State":
        pass

    @abstractmethod
    def approve(self, document: Document) -> "State":
        pass

    @abstractmethod
    def reject(self, document: Document) -> "State":
        pass

    @abstractmethod
    def writeable(self) -> bool:
        pass

    @abstractmethod
    def editable(self) -> bool:
        pass

    @abstractmethod
    def publishable(self) -> bool:
        pass


class DraftState(State):
    NAME = "Draft"

    def render(self, document: Document) -> str:
        return f"Draft: {document.content}"

    def publish(self, document: Document) -> "State":
        return ModerationState()

    def approve(self, document: Document) -> "State":
        return self

    def reject(self, document: Document) -> "State":
        return self

    def writeable(self) -> bool:
        return True

    def editable(self) -> bool:
        return True

    def publishable(self) -> bool:
        return True


class ModerationState(State):
    NAME = "Moderation"

    def render(self, document: Document) -> str:
        return f"Moderation: {document.content}"

    def publish(self, document: Document) -> "State":
        return self

    def approve(self, document: Document) -> "State":
        return PublishedState()

    def reject(self, document: Document) -> "State":
        return DraftState()

    def writeable(self) -> bool:
        return False

    def editable(self) -> bool:
        return False

    def publishable(self) -> bool:
        return False


class PublishedState(State):
    NAME = "Published"

    def render(self, document: Document) -> str:
        return f"Published: {document.content}"

    def publish(self, document: Document) -> "State":
        return self

    def approve(self, document: Document) -> "State":
        return self

    def reject(self, document: Document) -> "State":
        return self

    def writeable(self) -> bool:
        return False

    def editable(self) -> bool:
        return False

    def publishable(self) -> bool:
        return False


if __name__ == "__main__":
    doc = Document()

    doc.write("Hello, World!")
    print(doc.render())  # Draft: Hello, World!

    doc.publish()
    print(doc.render())  # Moderation: Hello, World!

    doc.approve()
    print(doc.render())  # Published: Hello, World!

    doc.write(" More text.")  # Document is not writeable in the current state.
    print(doc.render())  # Published: Hello, World!

    saved_data = doc.save()
    print(saved_data)  # {'content': 'Hello, World!', 'state': 'Published'}

    new_doc = Document.load(saved_data)
    print(new_doc.render())  # Published: Hello, World!
