"""
Intent:
Command is a behavioral design pattern that turns a request into a stand-alone object that
contains all information about the request. This transformation lets you parameterize methods with
different requests, delay or queue a request's execution, and support undoable operations.

Problem:
In many software systems, there is a need to decouple the sender of a request from the
receiver. This decoupling allows for more flexible and reusable code, as the sender does not need
to know the details of how the request will be handled. Additionally, there may be a need to
support features such as queuing requests, logging requests, or implementing undo functionality.
The Command pattern addresses these issues by encapsulating a request as an object, allowing for
greater flexibility and control over how requests are processed. This pattern is particularly useful in
scenarios where requests need to be executed at different times, in different orders, or by different
receivers.

Solution:
The Command pattern suggests creating a command interface that declares a method for executing a
request. Concrete command classes implement this interface and define the binding between a
receiver and an action. The client creates command objects and sets their receivers. The commands
are then passed to an invoker object, which is responsible for executing the commands. This
structure allows for the decoupling of the sender and receiver, as the invoker does not need to
know the details of how the command will be executed.

When to Use:
- When you want to decouple the sender of a request from its receiver.
- When you want to parameterize methods with different requests.
- When you want to support undoable operations.
- When you want to queue or log requests.
- When you want to implement a callback mechanism.
- When you want to support macro commands (a command that consists of multiple commands).
- When you want to encapsulate a request as an object, allowing for more flexible and reusable
    code.
- When you want to separate the responsibility of issuing a request from the responsibility of
    executing the request.
- When you want to implement a command pattern in a GUI application, where user actions can be
    represented as commands.
- When you want to implement a command pattern in a multi-threaded environment, where requests
    can be executed asynchronously.
- When you want to implement a command pattern in a distributed system, where requests can be
    sent over a network.

How to Implement:
1. Define a command interface with an execute method.
2. Create concrete command classes that implement the command interface and define the binding
    between a receiver and an action.
3. Create a receiver class that contains the actual business logic to perform the action.
4. Create an invoker class that holds a command and is responsible for executing it.
5. In the client code, create instances of the concrete command classes, set their receivers,
    and pass them to the invoker.
6. Optionally, implement additional features such as undo functionality, command queuing, or
    logging.
7. Consider implementing a macro command class that can execute multiple commands in sequence.
8. Ensure that the command objects are immutable, so that their state cannot be changed after
    they are created.
9. Consider using a command factory to create command objects, especially if there are many
    different types of commands.

Pros and Cons:
+ Decouples the sender of a request from its receiver.
+ Allows for more flexible and reusable code.
+ Supports features such as queuing, logging, and undo functionality.
+ Promotes the Single Responsibility Principle by separating the responsibility of issuing a
    request from the responsibility of executing the request.
- Can lead to a proliferation of command classes, which may impact maintainability.
- May introduce additional complexity due to the added layer of abstraction.
- Can lead to performance overhead due to the creation of command objects.
- May require careful design to ensure that commands are properly constructed and executed.

Real-world use cases:
- GUI Applications: In graphical user interfaces, user actions such as button clicks can be
    encapsulated as command objects, allowing for features like undo/redo and action logging.
- Transaction Management: In database systems, operations can be encapsulated as commands to
    support transaction management, including commit and rollback functionality.
- Job Scheduling Systems: In systems that schedule and execute jobs, commands can represent
    individual tasks, allowing for flexible scheduling and execution of jobs.
- Remote Procedure Calls (RPC): In distributed systems, commands can encapsulate requests sent
    over the network, allowing for decoupling between clients and servers.
"""

# Link: https://refactoring.guru/design-patterns/command


from abc import ABC, abstractmethod


# Receivers
class Light:
    def turn_on(self):
        print("The light is ON")

    def turn_off(self):
        print("The light is OFF")


class Thermostat:
    def __init__(self):
        self._temperature = 20  # Default temperature

    def set_temperature(self, temp):
        self._temperature = temp
        print(f"Thermostat set to {self._temperature}°C")

    def reset_temperature(self):
        self._temperature = 20
        print("Thermostat reset to default 20°C")


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class TurnOnLightCommand(Command):
    def __init__(self, light: Light):
        self._light = light

    def execute(self):
        self._light.turn_on()

    def undo(self):
        self._light.turn_off()


class TurnOffLightCommand(Command):
    def __init__(self, light: Light):
        self._light = light

    def execute(self):
        self._light.turn_off()

    def undo(self):
        self._light.turn_on()


class SetTemperatureCommand(Command):
    def __init__(self, thermostat: Thermostat, temp: int):
        self._thermostat = thermostat
        self._temp = temp
        self._prev_temp = thermostat._temperature

    def execute(self):
        self._thermostat.set_temperature(self._temp)

    def undo(self):
        self._thermostat.set_temperature(self._prev_temp)


# Macro Command
class MacroCommand(Command):
    def __init__(self, commands: list[Command]):
        self._commands = commands

    def execute(self):
        for command in self._commands:
            command.execute()

    def undo(self):
        for command in reversed(self._commands):
            command.undo()


# Invoker
class RemoteControl:
    def __init__(self):
        self._command = None

    def set_command(self, command: Command):
        self._command = command

    def press_execute(self):
        if self._command:
            self._command.execute()

    def press_undo(self):
        if self._command:
            self._command.undo()


# Client
def main():
    light = Light()
    thermostat = Thermostat()

    # Create commands
    light_on = TurnOnLightCommand(light)
    set_temp = SetTemperatureCommand(thermostat, 22)

    # Create macro command
    morning_routine = MacroCommand([light_on, set_temp])

    remote = RemoteControl()
    remote.set_command(morning_routine)

    print("Executing morning routine...")
    remote.press_execute()

    print("\nUndoing morning routine...")
    remote.press_undo()


if __name__ == "__main__":
    main()
