from typing import Any, Callable, Dict, List, Optional, Tuple

Predicate = Callable[[str, Any], bool]
Handler = Callable[[str, Any], None]
Teardown = Callable[[], None]


class EventBus:
    def __init__(self) -> None:
        # Maps topic -> list of (handler, predicate, teardown, teardown_called)
        self._subs: Dict[
            str, List[Tuple[Handler, Optional[Predicate], Optional[Teardown], bool]]
        ] = {}

    def subscribe(
        self,
        topic: str,
        handler: Handler,
        predicate: Optional[Predicate] = None,
        teardown: Optional[Teardown] = None,
    ) -> Callable[[], None]:
        """
        Returns an unsubscribe function.
        Topic supports wildcards: '*' (all) and 'user.*' (prefix).
        """
        if topic not in self._subs:
            self._subs[topic] = []
        self._subs[topic].append((handler, predicate, teardown, False))

        def unsubscribe() -> None:
            if topic in self._subs:
                new_list = []
                for h, p, t, called in self._subs[topic]:
                    if h == handler and p == predicate and t == teardown:
                        if t and not called:
                            try:
                                t()
                            finally:
                                called = True
                        # skip removing teardown twice
                    else:
                        new_list.append((h, p, t, called))
                if new_list:
                    self._subs[topic] = new_list
                else:
                    del self._subs[topic]

        return unsubscribe

    def publish(self, topic: str, data: Any) -> None:
        for sub_topic, handlers in list(self._subs.items()):
            if self._match(sub_topic, topic):
                for handler, predicate, _, _ in handlers:
                    if predicate is None or predicate(topic, data):
                        try:
                            handler(topic, data)
                        except Exception as e:
                            print(f"[publish] handler {handler.__name__} failed: {e}")

    def _match(self, sub_topic: str, pub_topic: str) -> bool:
        # Rules:
        # - '*' matches any topic
        # - 'user.*' matches 'user.created', 'user.deleted'
        # - exact match otherwise
        if sub_topic == "*":
            return True
        if sub_topic.endswith(".*"):
            prefix = sub_topic[:-2]
            return pub_topic.startswith(prefix + ".")
        return sub_topic == pub_topic


# ---------------- DEMO ----------------
if __name__ == "__main__":
    bus = EventBus()

    # Handlers
    def handler1(topic: str, data: Any) -> None:
        print(f"Handler1 received on {topic}: {data}")

    def handler2(topic: str, data: Any) -> None:
        print(f"Handler2 received on {topic}: {data}")

    def faulty_handler(topic: str, data: Any) -> None:
        raise RuntimeError("Boom! Something went wrong")

    def predicate(topic: str, data: Any) -> bool:
        return data.get("value", 0) > 10

    # Logging observer for order.* only
    def logging_observer(topic: str, data: Any) -> None:
        print(f"[LOGGER] {topic} -> {data}")

    # Subscribe
    unsubscribe1 = bus.subscribe("user.created", handler1)
    unsubscribe2 = bus.subscribe("user.*", handler2, predicate=predicate)
    unsubscribe3 = bus.subscribe("user.deleted", faulty_handler)
    unsubscribe4 = bus.subscribe("order.*", logging_observer)

    # Publish events
    print("\n--- Publishing events ---")
    bus.publish("user.created", {"id": 1, "value": 5})  # Only handler1
    bus.publish("user.deleted", {"id": 2, "value": 15})  # handler2 + faulty_handler
    bus.publish("user.created", {"id": 3, "value": 20})  # handler1 + handler2
    bus.publish("order.created", {"id": 4, "value": 20})  # logger only

    # Unsubscribe handler1
    print("\n--- After unsubscribe1 ---")
    unsubscribe1()
    bus.publish("user.created", {"id": 5, "value": 25})  # Only handler2

    # Unsubscribe logger
    print("\n--- After unsubscribe4 ---")
    unsubscribe4()
    bus.publish("order.created", {"id": 6, "value": 30})  # No logger now
