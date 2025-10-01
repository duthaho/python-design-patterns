from dataclasses import dataclass, field
from typing import Protocol


# -------------------------
# User
# -------------------------
@dataclass
class User:
    user_id: int
    name: str
    role: str  # "member" | "moderator" | "admin"
    inbox: list[str] = field(default_factory=list)

    def receive(self, message: str) -> None:
        self.inbox.append(message)
        print(f"[{self.name}] <- {message}")


# -------------------------
# Policy Interface
# -------------------------
class Policy(Protocol):
    def check(self, sender: User, text: str) -> tuple[bool, str | None]: ...


# -------------------------
# Example Policies
# -------------------------
class MutePolicy:
    def __init__(self, muted: set[int]) -> None:
        self.muted = muted

    def check(self, sender: User, text: str) -> tuple[bool, str | None]:
        if sender.user_id in self.muted:
            return False, "You are muted and cannot send messages."
        return True, None


class BannedWordPolicy:
    def __init__(self, banned_words: set[str]) -> None:
        self.banned_words = {w.lower() for w in banned_words}

    def check(self, sender: User, text: str) -> tuple[bool, str | None]:
        lowered = text.lower()
        if any(bad in lowered for bad in self.banned_words):
            return False, "Your message contained banned words and was blocked."
        return True, None


class MaxLengthPolicy:
    def __init__(self, max_len: int) -> None:
        self.max_len = max_len

    def check(self, sender: User, text: str) -> tuple[bool, str | None]:
        if len(text) > self.max_len:
            return False, f"Message too long (>{self.max_len} chars)."
        return True, None


# -------------------------
# Mediator
# -------------------------
class ChatMediator:
    def __init__(self) -> None:
        self.users: dict[int, User] = {}
        self.muted: set[int] = set()
        self.banned_users: set[int] = set()
        self.policies: list[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        self.policies.append(policy)

    def join(self, user: User) -> None:
        if user.user_id in self.banned_users:
            print(f"[System] {user.name} is banned and cannot join the chat.")
            return
        self.users[user.user_id] = user
        print(f"[System] {user.name} joined the chat.")

    def leave(self, user_id: int) -> None:
        if user_id in self.users:
            user = self.users.pop(user_id)
            print(f"[System] {user.name} left the chat.")
        else:
            print(f"[System] User with ID {user_id} not found in chat.")

    def _check_policies(self, sender: User, text: str) -> bool:
        for policy in self.policies:
            ok, reason = policy.check(sender, text)
            if not ok:
                sender.receive(f"[System] {reason}")
                return False
        return True

    def send_public(self, sender_id: int, text: str) -> None:
        if sender_id not in self.users:
            print("[System] Invalid sender.")
            return

        sender = self.users[sender_id]
        if not self._check_policies(sender, text):
            return

        for user in self.users.values():
            if user.user_id != sender_id:
                user.receive(f"{sender.name}: {text}")

    def send_private(self, sender_id: int, recipient_id: int, text: str) -> None:
        if sender_id not in self.users:
            print("[System] Invalid sender.")
            return

        sender = self.users[sender_id]
        if recipient_id not in self.users:
            sender.receive("[System] Recipient not found.")
            return

        if not self._check_policies(sender, text):
            return

        recipient = self.users[recipient_id]
        recipient.receive(f"DM from {sender.name}: {text}")

    def mute(self, moderator_id: int, target_id: int) -> None:
        if moderator_id not in self.users or target_id not in self.users:
            print("[System] Invalid user ID.")
            return

        moderator = self.users[moderator_id]
        target = self.users[target_id]

        if moderator.role not in {"moderator", "admin"}:
            print(f"[System] {moderator.name} does not have permission to mute users.")
            return

        self.muted.add(target_id)
        print(f"[System] {target.name} has been muted by {moderator.name}.")

    def ban(self, admin_id: int, target_id: int) -> None:
        if admin_id not in self.users or target_id not in self.users:
            print("[System] Invalid user ID.")
            return

        admin = self.users[admin_id]
        target = self.users[target_id]

        if admin.role != "admin":
            print(f"[System] {admin.name} does not have permission to ban users.")
            return

        self.banned_users.add(target_id)
        print(f"[System] {target.name} has been banned by {admin.name}.")
        if target_id in self.users:
            self.leave(target_id)


# -------------------------
# Demo
# -------------------------
def demo():
    chat = ChatMediator()

    # Attach policies
    chat.add_policy(MutePolicy(chat.muted))
    chat.add_policy(BannedWordPolicy({"spam", "scam"}))
    chat.add_policy(MaxLengthPolicy(50))

    alice = User(1, "Alice", "member")
    mod = User(2, "Mod", "moderator")
    admin = User(3, "Root", "admin")

    chat.join(alice)
    chat.join(mod)
    chat.join(admin)

    chat.send_public(1, "hello everyone")
    chat.send_public(
        1,
        "this message is way toooooooooooooooooooooooooooooooooooooooooooooooooo long",
    )
    chat.mute(2, 1)
    chat.send_public(1, "this will be dropped")
    chat.send_private(3, 1, "DM from admin")
    chat.ban(3, 1)
    chat.join(alice)  # should be denied while banned


if __name__ == "__main__":
    demo()
