"""
Intent:
Chain of Responsibility is a behavioral design pattern that lets you pass requests along a chain of
handlers. Upon receiving a request, each handler decides either to process the request or to pass it
to the next handler in the chain. This pattern decouples the sender of a request from its receiver,
giving more than one object a chance to handle the request.

Problem:
In a system where multiple objects can handle a request, it can be challenging to determine which
object should process it. Hardcoding the logic to select the appropriate handler can lead to
rigid and inflexible code. Additionally, if the set of handlers changes frequently, maintaining
the selection logic can become cumbersome. The Chain of Responsibility pattern addresses these issues by
allowing multiple handlers to process a request without the sender needing to know which handler
will ultimately handle it.

Solution:
The Chain of Responsibility pattern suggests creating a chain of handler objects, each capable of
handling a specific type of request. Each handler has a reference to the next handler in the chain.
When a request is received, the first handler in the chain checks if it can process the request.
If it can, it handles the request; if not, it passes the request to the next handler in the chain.
This continues until a handler processes the request or the end of the chain is reached.

When to Use:
- When multiple objects can handle a request, and the specific handler is not known in advance.
- When you want to decouple the sender of a request from its receiver.
- When you want to add or change handlers dynamically without affecting the client code.
- When you want to avoid coupling the sender of a request to a specific handler class.
- When you want to implement a flexible and extensible request processing system.
- When you want to allow multiple handlers to process a request in a specific order.
- When you want to implement a chain of processing steps, where each step can modify or handle
    the request.

How to Implement:
1. Define a common interface for all handlers in the chain, including a method to set the
    next handler and a method to handle the request.
2. Create concrete handler classes that implement the common interface. Each handler should
    implement the logic to determine if it can handle the request and, if not, pass it to the next
    handler.
3. In the client code, create instances of the concrete handlers and link them together to form
    a chain.
4. Send requests to the first handler in the chain. The request will be passed along the chain
    until it is handled or reaches the end of the chain.
5. Optionally, implement different types of handlers for various request types or processing
    steps.
6. Ensure that the chain can be modified dynamically, allowing handlers to be added, removed,
    or reordered as needed.
7. Consider implementing a default handler at the end of the chain to handle requests that
    are not processed by any other handler.

Pros and Cons:
+ Decouples the sender of a request from its receiver.
+ Allows multiple handlers to process a request.
+ Makes it easy to add or change handlers without affecting the client code.
+ Promotes the Single Responsibility Principle by allowing each handler to focus on a specific
    type of request.
- Can lead to a long chain of handlers, which may impact performance.
- May make debugging more difficult due to the added layer of indirection.
- Can lead to unhandled requests if no handler in the chain can process the request.
- May require careful design to ensure that the chain is properly constructed and maintained.

Real-world use cases:
- Event Handling Systems: In GUI frameworks, events such as mouse clicks or key presses can be
    passed through a chain of event handlers, allowing different components to respond to the same
    event.
- Logging Frameworks: A logging system can use a chain of responsibility to pass log messages
    through multiple loggers, each responsible for handling different log levels or output formats.
- Customer Support Systems: In customer support applications, a support request can be passed
    through a chain of support agents, each with different levels of expertise, until it reaches
    an agent who can resolve the issue.
- Middleware in Web Servers: Web servers often use a chain of middleware components to process
    incoming HTTP requests, allowing each component to handle specific aspects such as
    authentication, logging, or data transformation.
- Validation Chains: In data validation scenarios, a chain of validators can be used to check
    different aspects of the data, passing it along the chain until it is either validated or
    rejected.
- Technical Support Escalation: In technical support systems, a support ticket can be escalated
    through a chain of support levels, from front-line support to specialized technicians, until
    the issue is resolved.
- Approval Workflows: In business applications, an approval request can be passed through a chain
    of approvers, each with the authority to approve or reject the request based on specific criteria
    or thresholds.
"""

# Link: https://refactoring.guru/design-patterns/chain-of-responsibility


from abc import ABC, abstractmethod


class Handler(ABC):
    _next_handler: "Handler" = None

    def set_next(self, handler: "Handler") -> "Handler":
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: dict) -> dict:
        if self._next_handler:
            return self._next_handler.handle(request)
        return None


class InfoHandler(Handler):
    def handle(self, request: dict) -> dict:
        if request.get("type") == "info":
            return {"status": "info", "message": "This is an informational message."}
        return super().handle(request)


class WarningHandler(Handler):
    def handle(self, request: dict) -> dict:
        if request.get("type") == "warning":
            return {"status": "warning", "message": "This is a warning message."}
        return super().handle(request)


class ErrorHandler(Handler):
    def handle(self, request: dict) -> dict:
        if request.get("type") == "error":
            return {"status": "error", "message": "This is an error message."}
        return super().handle(request)


def client_code(handler: Handler, requests: list[dict]):
    for request in requests:
        print(f"\nClient: Who wants to handle {request}?")
        result = handler.handle(request)
        if result:
            print(f"  {result['status'].upper()}: {result['message']}")
        else:
            print(f"  {request['type'].upper()}: No handler found.")


if __name__ == "__main__":
    info_handler = InfoHandler()
    warning_handler = WarningHandler()
    error_handler = ErrorHandler()

    info_handler.set_next(warning_handler).set_next(error_handler)

    requests = [
        {"type": "info"},
        {"type": "warning"},
        {"type": "error"},
        {"type": "debug"},
    ]

    client_code(info_handler, requests)
