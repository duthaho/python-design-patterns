"""
Intent:
Provide a unified interface to a set of interfaces in a subsystem. Facade defines a higher-level
interface that makes the subsystem easier to use.

Problem:
Imagine you’re developing a complex home theater system that includes various components like a
DVD player, projector, sound system, and lighting. Each component has its own interface and
methods for operation. If a user wants to watch a movie, they would need to interact with each
component individually, which can be complicated and overwhelming.

Solution:
The Facade pattern suggests creating a simplified interface that provides a unified way to
interact with the complex subsystem. This facade interface would encapsulate the interactions
with the various components, allowing users to perform high-level operations without needing to
understand the details of each component.

When to use:
- When you want to provide a simple interface to a complex subsystem.
- When you want to decouple a client from a complex subsystem.
- When you want to improve code readability and maintainability by reducing dependencies.
- When you want to layer your subsystems, using facades to define entry points.

How to implement:
1. Identify the complex subsystem that you want to simplify.
2. Create a facade class that provides a simplified interface to the subsystem. This class should
    contain methods that represent high-level operations that users can perform.
3. Inside the facade class, maintain references to the various components of the subsystem.
4. Implement the methods in the facade class to coordinate interactions with the subsystem
    components, delegating tasks as necessary.
5. Use the facade class in your client code to interact with the subsystem through the simplified
    interface.

Pros and Cons:
+ Simplifies the interface to a complex subsystem, making it easier to use.
+ Reduces dependencies between the client and the subsystem, promoting loose coupling.
+ Improves code readability and maintainability by providing a clear entry point to the subsystem.
- Can introduce an additional layer of abstraction, which may add complexity.
- May lead to a less flexible design if the facade does not expose all necessary functionality of
    the subsystem.
- Can become a "god object" if it tries to handle too many responsibilities.

Real-world use cases:
- In software libraries, facades are often used to provide a simplified interface to complex
    subsystems, such as database access or networking.
- In web development, a facade can be used to provide a unified API for interacting with multiple
    backend services.
- In home automation systems, a facade can provide a single interface to control various devices
    like lights, thermostats, and security systems.
"""

# Link: https://refactoring.guru/design-patterns/facade


from abc import ABC, abstractmethod


class DVDPlayer:
    def on(self):
        print("DVD Player is ON")

    def play(self, movie):
        print(f"Playing movie: {movie}")

    def stop(self):
        print("Stopping the movie")

    def off(self):
        print("DVD Player is OFF")


class Projector:
    def on(self):
        print("Projector is ON")

    def set_input(self, input_source):
        print(f"Projector input set to: {input_source}")

    def wide_screen_mode(self):
        print("Projector in widescreen mode")

    def off(self):
        print("Projector is OFF")


class SoundSystem:
    def on(self):
        print("Sound System is ON")

    def set_volume(self, level):
        print(f"Sound System volume set to: {level}")

    def off(self):
        print("Sound System is OFF")


class HomeTheaterFacade:
    def __init__(
        self, dvd_player: DVDPlayer, projector: Projector, sound_system: SoundSystem
    ) -> None:
        self.dvd_player = dvd_player
        self.projector = projector
        self.sound_system = sound_system

    def watch_movie(self, movie: str) -> None:
        print("Get ready to watch a movie...")
        self.dvd_player.on()
        self.dvd_player.play(movie)
        self.projector.on()
        self.projector.set_input("DVD")
        self.projector.wide_screen_mode()
        self.sound_system.on()
        self.sound_system.set_volume(5)

    def end_movie(self) -> None:
        print("Shutting down the home theater...")
        self.dvd_player.stop()
        self.dvd_player.off()
        self.projector.off()
        self.sound_system.off()


if __name__ == "__main__":
    dvd_player = DVDPlayer()
    projector = Projector()
    sound_system = SoundSystem()

    home_theater = HomeTheaterFacade(dvd_player, projector, sound_system)
    home_theater.watch_movie("Inception")
    print()
    home_theater.end_movie()
