"""
Intent:
Proxy is a structural design pattern that lets you provide a substitute or placeholder for another
object. A proxy controls access to the original object, allowing you to perform something either
before or after the request gets through to the original object.

Problem:
Some objects are more expensive to create than others (in terms of memory, processing time, etc.).
Sometimes you want to delay the creation of such objects until you actually need them. Other times,
you want to add some additional logic when an object is accessed, like logging, access control,
or caching.

Solution:
The Proxy pattern suggests creating a separate proxy class that has the same interface as the
original class. The proxy class holds a reference to the original object and controls access to it.
When a client calls a method on the proxy, the proxy can perform additional actions before or after
delegating the call to the original object.

When to Use:
- When you want to control access to an object, for example, to add logging, access control, or
    caching.
- When you want to delay the creation of an expensive object until it's actually needed (lazy
    loading).
- When you want to provide a simplified interface to a complex object.
- When you want to add functionality to an object without changing its code.
- When you want to manage the lifecycle of an object, such as reference counting or resource
    management.

How to Implement:
1. Define a common interface for both the original object and the proxy.
2. Create the original class that implements the common interface.
3. Create the proxy class that also implements the common interface and holds a reference to the
    original object.
4. In the proxy class, implement the methods to perform additional actions before or after
    delegating the calls to the original object.
5. In the client code, use the proxy class instead of the original class to interact with the object.
6. Optionally, implement different types of proxies, such as virtual proxies (for lazy loading),
    protection proxies (for access control), or smart references (for additional functionality).
7. Ensure that the proxy class is transparent to the client, meaning the client should not be aware
    that it is dealing with a proxy instead of the original object.

Pros and Cons:
+ Provides a way to control access to an object.
+ Can add additional functionality without changing the original object's code.
+ Can improve performance by delaying the creation of expensive objects.
- Introduces additional complexity with the proxy class.
- May lead to increased memory usage if many proxy objects are created.
- Can make debugging more difficult due to the added layer of indirection.

Real-world use cases:
- Virtual Proxy: In image loading applications, a virtual proxy can be used to load images only
    when they are actually needed, improving performance and reducing memory usage.
- Protection Proxy: In secure systems, a protection proxy can control access to sensitive data or
    operations based on user permissions.
- Remote Proxy: In distributed systems, a remote proxy can represent an object located in a
    different address space, handling communication and serialization.
- Smart Reference: In resource management systems, a smart reference proxy can manage the lifecycle
    of an object, such as reference counting or lazy initialization.
- Caching Proxy: In web applications, a caching proxy can store the results of expensive operations
    to improve performance for subsequent requests.
- Logging Proxy: In debugging or monitoring systems, a logging proxy can log method calls and
    parameters for analysis.
- Firewall Proxy: In network security, a firewall proxy can filter incoming and outgoing traffic
    based on predefined security rules.
- API Gateway: In microservices architectures, an API gateway can act as a proxy to route requests
    to the appropriate microservice, handle authentication, and perform rate limiting.
"""

# Link: https://refactoring.guru/design-patterns/proxy


from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class UserRole(Enum):
    ADMIN = "ADMIN"
    GUEST = "GUEST"


@dataclass(frozen=True)
class User:
    name: str
    role: UserRole


class File(ABC):
    @abstractmethod
    def read_content(self, user: User) -> str:
        pass


class RealFile(File):
    def __init__(self, filename: str):
        self.filename = filename
        self._load_file()

    def _load_file(self):
        print(f"Loading file '{self.filename}' from disk...")

    def read_content(self, user: User) -> str:
        return f"Content of the file '{self.filename}'."


class FileProtectedProxy(File):
    def __init__(self, filename: str):
        self.filename = filename
        self._real_file = None

    def _get_real_file(self) -> RealFile:
        if self._real_file is None:
            self._real_file = RealFile(self.filename)
        return self._real_file

    def read_content(self, user: User) -> str:
        if user.role != UserRole.ADMIN:
            raise PermissionError("Access denied. Only admins can read the file.")
        
        real_file = self._get_real_file()
        return real_file.read_content(user)


def main() -> None:
    admin_user = User(name="Alice", role=UserRole.ADMIN)
    guest_user = User(name="Bob", role=UserRole.GUEST)

    protected_file = FileProtectedProxy("example.txt")

    print(f"Admin trying to read the file: {protected_file.read_content(admin_user)}")
    print(f"Guest trying to read the file: {protected_file.read_content(guest_user)}")


if __name__ == "__main__":
    main()
