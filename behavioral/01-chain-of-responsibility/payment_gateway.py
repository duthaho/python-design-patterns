import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional


class Payment:
    def __init__(self, amount: float, card: str):
        self.amount = amount
        self.card = card


class AsyncHandler(ABC):
    def __init__(self, timeout: float | None = None):
        self._next: Optional["AsyncHandler"] = None
        self.timeout = timeout

    def set_next(self, h: "AsyncHandler") -> "AsyncHandler":
        self._next = h
        return h

    async def _forward(self, payment: Payment) -> Dict:
        if self._next:
            return await self._next.handle(payment)
        return {"status": "failed", "reason": "exhausted"}

    @abstractmethod
    async def handle(self, payment: Payment) -> Dict: ...


class FraudScorer(AsyncHandler):
    def __init__(self, scorer, threshold: float, timeout: float | None = None):
        super().__init__(timeout)
        self.scorer = scorer
        self.threshold = threshold

    async def handle(self, payment: Payment) -> Dict:
        # TODO: await scorer(payment); if risk > threshold -> blocked; else forward
        risk = await asyncio.wait_for(self.scorer(payment), timeout=self.timeout)
        if risk > self.threshold:
            return {"status": "blocked", "reason": "fraud"}
        
        return await self._forward(payment)


class PrimaryGateway(AsyncHandler):
    def __init__(self, api_call, timeout: float | None = None):
        super().__init__(timeout)
        self.api_call = api_call

    async def handle(self, payment: Payment) -> Dict:
        # TODO: try await api_call(payment) within timeout; on success return authorized
        # on error or timeout, forward
        try:
            await asyncio.wait_for(self.api_call(payment), timeout=self.timeout)
            return {"status": "authorized"}
        except (asyncio.TimeoutError, RuntimeError):
            pass

        return await self._forward(payment)


class SecondaryGateway(AsyncHandler):
    def __init__(self, api_call, timeout: float | None = None):
        super().__init__(timeout)
        self.api_call = api_call

    async def handle(self, payment: Payment) -> Dict:
        # TODO: same pattern as primary
        try:
            await asyncio.wait_for(self.api_call(payment), timeout=self.timeout)
            return {"status": "authorized"}
        except (asyncio.TimeoutError, RuntimeError):
            return {"status": "failed", "reason": "gateway error"}


async def fake_scorer(payment: Payment) -> float:
    await asyncio.sleep(0.05)
    return 0.9 if payment.amount > 500 else 0.1


async def flaky_api(payment: Payment) -> None:
    # simulate delays/failures based on card suffix
    if payment.card.endswith("00"):
        await asyncio.sleep(0.2)
        raise RuntimeError("gateway error")
    if payment.card.endswith("99"):
        await asyncio.sleep(1.0)  # likely to timeout
    await asyncio.sleep(0.1)
    return None


async def reliable_api(payment: Payment) -> None:
    await asyncio.sleep(0.2)
    return None


async def main():
    fraud = FraudScorer(fake_scorer, threshold=0.7, timeout=0.2)
    primary = PrimaryGateway(flaky_api, timeout=0.3)
    secondary = SecondaryGateway(reliable_api, timeout=0.5)
    fraud.set_next(primary).set_next(secondary)

    cases = [
        Payment(50, "****-****-****-10"),  # should pass fraud, primary OK
        Payment(50, "****-****-****-99"),  # primary timeout -> secondary
        Payment(600, "****-****-****-10"),  # blocked by fraud
        Payment(50, "****-****-****-00"),  # primary error -> secondary
    ]
    for p in cases:
        res = await fraud.handle(p)
        print(p.card[-2:], "->", res)


if __name__ == "__main__":
    asyncio.run(main())
