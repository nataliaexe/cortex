"""Small dependency-free metrics registry for the local API."""
from collections import Counter


class Metrics:
    def __init__(self): self._counters: Counter[str] = Counter()
    def increment(self, name: str) -> None: self._counters[name] += 1
    def prometheus(self) -> str:
        return "".join(f"cortex_{name}_total {value}\n" for name, value in sorted(self._counters.items()))


metrics = Metrics()
